"""Read-only comparison of a pg_restore data script and an isolated local restore.

This verifier does not execute the source SQL or restore anything. It supports
public ordinary-table COPY data and sequence states used by NeuroLab's schema.
Connection credentials are read from an environment variable, never printed.
"""

import argparse
import hashlib
import json
import os
import re
import stat
from dataclasses import dataclass
from pathlib import Path

import psycopg
from psycopg import sql
from psycopg.conninfo import conninfo_to_dict

IDENTIFIER = rb'(?:[a-z_][a-z0-9_]*|"[a-z_][a-z0-9_]*")'
COPY_HEADER = re.compile(
    rb'COPY (?:public|"public")\.(' + IDENTIFIER + rb") "
    rb"\((" + IDENTIFIER + rb"(?:, " + IDENTIFIER + rb")*)\) FROM stdin;"
)
SEQUENCE_STATE = re.compile(
    rb"SELECT pg_catalog\.setval\('"
    + rb'(?:public|"public")\.('
    + IDENTIFIER
    + rb")', (-?[0-9]+), (true|false)\);"
)
MAX_DATA_BYTES = 128 * 1024 * 1024
READ_ONLY_OPTIONS = "-c default_transaction_read_only=on -c statement_timeout=15000"


@dataclass(frozen=True)
class TableSnapshot:
    columns: tuple[str, ...]
    row_count: int
    sha256: str


@dataclass(frozen=True)
class DumpSnapshot:
    tables: dict[str, TableSnapshot]
    sequences: dict[str, tuple[int, bool]]


def fingerprint(rows: list[bytes]) -> tuple[int, str]:
    digest = hashlib.sha256()
    for row in sorted(rows):
        digest.update(row)
        digest.update(b"\n")
    return len(rows), digest.hexdigest()


def parse_table(header: bytes, lines) -> tuple[str, TableSnapshot]:
    match = COPY_HEADER.fullmatch(header)
    if not match:
        raise ValueError("Unsupported COPY header; expected public ordinary tables")
    name = match[1].decode("ascii").strip('"')
    columns = tuple(column.strip('"') for column in match[2].decode("ascii").split(", "))
    if len(set(columns)) != len(columns):
        raise ValueError("Duplicate COPY columns")
    rows = []
    for line in lines:
        if line == b"\\.":
            count, digest = fingerprint(rows)
            return name, TableSnapshot(columns, count, digest)
        if len(line.split(b"\t")) != len(columns):
            raise ValueError("COPY column count mismatch")
        rows.append(line)
    raise ValueError("Unterminated COPY data")


def parse_dump(data: bytes) -> DumpSnapshot:
    if len(data) > MAX_DATA_BYTES:
        raise ValueError("Data script exceeds verification limit")
    tables = {}
    sequences = {}
    lines = iter(data.split(b"\n"))
    for line in lines:
        if line.startswith(b"COPY "):
            name, snapshot = parse_table(line, lines)
            if name in tables:
                raise ValueError("Duplicate COPY table")
            tables[name] = snapshot
        elif line.startswith(b"SELECT pg_catalog.setval("):
            match = SEQUENCE_STATE.fullmatch(line)
            if not match or match[1].decode("ascii").strip('"') in sequences:
                raise ValueError("Unsupported or duplicate sequence state")
            sequences[match[1].decode("ascii").strip('"')] = (int(match[2]), match[3] == b"true")
        elif line.startswith((b"INSERT ", b"UPDATE ", b"DELETE ", b"SELECT pg_catalog.lo_")):
            raise ValueError("Unsupported data format or large objects")
    if not tables:
        raise ValueError("No public COPY tables found")
    return DumpSnapshot(tables, sequences)


def local_restore_parameters(dsn: str) -> dict:
    parameters = conninfo_to_dict(dsn)
    if any(os.environ.get(key) for key in ("PGHOSTADDR", "PGSERVICE", "PGSERVICEFILE")):
        raise ValueError("Ambient connection redirection is not supported")
    if any(key in parameters for key in ("hostaddr", "service", "servicefile")):
        raise ValueError("Connection redirection is not supported")
    host = Path(parameters.get("host", ""))
    if not host.is_absolute() or not host.is_dir():
        raise ValueError("An existing private Unix socket directory is required")
    metadata = host.stat()
    if metadata.st_uid != os.getuid() or stat.S_IMODE(metadata.st_mode) & 0o077:
        raise ValueError("Socket directory must be owned by this user and private")
    if not parameters.get("dbname", "").startswith("neurolab_restore_"):
        raise ValueError("Only a named isolated rehearsal database is accepted")
    parameters.update(connect_timeout="5", options=READ_ONLY_OPTIONS)
    return parameters


def verify_restored(snapshot: DumpSnapshot, connection) -> dict:
    if connection.execute("SHOW transaction_read_only").fetchone()[0] != "on":
        raise ValueError("Read-only connection required")
    names = connection.execute(
        "SELECT table_name FROM information_schema.tables "
        "WHERE table_schema='public' AND table_type='BASE TABLE'"
    ).fetchall()
    if {row[0] for row in names} != set(snapshot.tables):
        raise ValueError("Public table inventory differs from the export")
    for name, expected in snapshot.tables.items():
        columns = connection.execute(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_schema='public' AND table_name=%s ORDER BY ordinal_position",
            (name,),
        ).fetchall()
        if tuple(row[0] for row in columns) != expected.columns:
            raise ValueError(f"Column inventory differs: {name}")
        query = sql.SQL("COPY {} ({}) TO STDOUT").format(
            sql.Identifier("public", name),
            sql.SQL(", ").join(sql.Identifier(column) for column in expected.columns),
        )
        with connection.cursor().copy(query) as copy:
            data = b"".join(bytes(chunk) for chunk in copy)
        rows = data.split(b"\n")[:-1] if data else []
        if fingerprint(rows) != (expected.row_count, expected.sha256):
            raise ValueError(f"Table content differs: {name}")
    verify_sequences(snapshot, connection)
    return {
        "all_table_counts_and_content_digests_match": True,
        "sequence_states_match": True,
        "read_only": True,
        "tables": {name: table.row_count for name, table in snapshot.tables.items()},
        "sequence_count": len(snapshot.sequences),
    }


def verify_sequences(snapshot: DumpSnapshot, connection) -> None:
    names = connection.execute(
        "SELECT sequencename FROM pg_sequences WHERE schemaname='public'"
    ).fetchall()
    if {row[0] for row in names} != set(snapshot.sequences):
        raise ValueError("Public sequence inventory differs from the export")
    for name, expected in snapshot.sequences.items():
        actual = connection.execute(
            sql.SQL("SELECT last_value, is_called FROM {}").format(sql.Identifier("public", name))
        ).fetchone()
        if tuple(actual) != expected:
            raise ValueError(f"Sequence state differs: {name}")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dump-data", type=Path, required=True)
    parser.add_argument("--database-env", default="RESTORE_DATABASE_URL")
    arguments = parser.parse_args(argv)
    try:
        if arguments.dump_data.stat().st_size > MAX_DATA_BYTES:
            raise ValueError("Data script exceeds verification limit")
        snapshot = parse_dump(arguments.dump_data.read_bytes())
        parameters = local_restore_parameters(os.environ.get(arguments.database_env, ""))
        with psycopg.connect(**parameters) as connection:
            result = verify_restored(snapshot, connection)
        print(json.dumps(result, indent=2))
        return 0
    except (OSError, ValueError, psycopg.Error):
        # Data scripts and connection errors can contain credentials or row values.
        print("Restore verification failed; inspect the private operator context.")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
