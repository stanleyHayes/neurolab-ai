"""Offline restore verification contracts; fixtures contain no production data."""

import contextlib
import io
import os
import secrets
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

from psycopg.conninfo import make_conninfo

from scripts.verify_postgres_restore import (
    READ_ONLY_OPTIONS,
    fingerprint,
    local_restore_parameters,
    main,
    parse_dump,
    verify_restored,
)

DUMP = (
    b"-- pg_restore fixture\nCOPY public.users (id, note) FROM stdin;\n"
    b"b\t\\N\na\thi\\nthere\n\\.\n"
    b"COPY public.empty (id) FROM stdin;\n\\.\n"
    b"SELECT pg_catalog.setval('public.events_seq', 3, true);\n"
)


@contextlib.contextmanager
def copied(chunks):
    yield chunks


def restored_connection():
    connection = MagicMock()
    values = [
        Mock(fetchone=lambda: ("on",)),
        Mock(fetchall=lambda: [("users",), ("empty",)]),
        Mock(fetchall=lambda: [("id",), ("note",)]),
        Mock(fetchall=lambda: [("id",)]),
        Mock(fetchall=lambda: [("events_seq",)]),
        Mock(fetchone=lambda: (3, True)),
    ]
    connection.execute.side_effect = values
    connection.cursor.return_value.copy.side_effect = [
        copied([b"a\thi\\nthere\n", b"b\t\\N\n"]),
        copied([]),
    ]
    connection.__enter__.return_value = connection
    return connection, values


class RestoreVerificationTests(unittest.TestCase):
    def test_copy_fingerprints_ignore_order_but_keep_null_empty_and_escaping(self):
        snapshot = parse_dump(DUMP)
        self.assertEqual(snapshot.tables["users"].row_count, 2)
        self.assertEqual(snapshot.tables["empty"].row_count, 0)
        self.assertEqual(snapshot.sequences, {"events_seq": (3, True)})
        self.assertEqual(fingerprint([b"a", b"b"]), fingerprint([b"b", b"a"]))
        self.assertNotEqual(fingerprint([b""]), fingerprint([]))
        self.assertNotEqual(fingerprint([b"\\N"]), fingerprint([b""]))
        self.assertNotEqual(fingerprint([b"a\\tb"]), fingerprint([b"a\tb"]))

    def test_supports_render_quote_all_identifiers_without_changing_names(self):
        data = b'COPY "public"."users" ("id", "note") FROM stdin;\nx\t\\N\n\\.\n'
        data += b'SELECT pg_catalog.setval(\'"public"."events_seq"\', 1, false);\n'
        snapshot = parse_dump(data)
        self.assertEqual(snapshot.tables["users"].columns, ("id", "note"))
        self.assertEqual(snapshot.tables["users"].row_count, 1)
        self.assertEqual(snapshot.sequences, {"events_seq": (1, False)})

    def test_rejects_partial_ambiguous_and_unsupported_source_formats(self):
        cases = [
            b"-- no table data",
            b"COPY private.users (id) FROM stdin;\nx\n\\.\n",
            b"COPY public.users (id) FROM stdin;\nx\n",
            b"COPY public.users (id, note) FROM stdin;\nx\n\\.\n",
            b"COPY public.users (id, id) FROM stdin;\nx\tx\n\\.\n",
            DUMP + b"COPY public.users (id) FROM stdin;\n\\.\n",
            DUMP + b"SELECT pg_catalog.setval('public.events_seq', 3, false);\n",
            DUMP + b"SELECT pg_catalog.setval('private.sequence', 3, true);\n",
            DUMP + b"INSERT INTO public.users VALUES ('x');\n",
            DUMP + b"SELECT pg_catalog.lo_create(1);\n",
        ]
        for data in cases:
            with self.subTest(data=data), self.assertRaises(ValueError):
                parse_dump(data)
        with (
            patch("scripts.verify_postgres_restore.MAX_DATA_BYTES", 10),
            self.assertRaises(ValueError),
        ):
            parse_dump(DUMP)

    def test_requires_a_private_owned_local_socket_and_rehearsal_database(self):
        with tempfile.TemporaryDirectory() as temporary, patch.dict(os.environ, {}, clear=True):
            host = Path(temporary)
            dsn = make_conninfo(host=str(host), dbname="neurolab_restore_fixture", user="fixture")
            self.assertEqual(local_restore_parameters(dsn)["options"], READ_ONLY_OPTIONS)
            host.chmod(0o755)
            with self.assertRaises(ValueError):
                local_restore_parameters(dsn)
            host.chmod(0o700)
            with (
                patch("scripts.verify_postgres_restore.os.getuid", return_value=-1),
                self.assertRaises(ValueError),
            ):
                local_restore_parameters(dsn)
            for key, value in [
                ("dbname", "production"),
                ("host", "127.0.0.1"),
                ("hostaddr", "203.0.113.1"),
                ("service", "production"),
            ]:
                candidate = make_conninfo(dsn, **{key: value})
                with self.subTest(key=key), self.assertRaises(ValueError):
                    local_restore_parameters(candidate)
            for variable in ["PGHOSTADDR", "PGSERVICE", "PGSERVICEFILE"]:
                with patch.dict(os.environ, {variable: "fixture"}), self.assertRaises(ValueError):
                    local_restore_parameters(dsn)

    def test_compares_every_table_column_value_and_sequence_without_writes(self):
        snapshot = parse_dump(DUMP)
        connection, _ = restored_connection()
        result = verify_restored(snapshot, connection)
        self.assertTrue(result["all_table_counts_and_content_digests_match"])
        self.assertTrue(result["sequence_states_match"])
        self.assertEqual(result["tables"], {"users": 2, "empty": 0})
        for call in connection.execute.call_args_list:
            query = call.args[0]
            text = query if isinstance(query, str) else query.as_string()
            self.assertTrue(text.startswith(("SELECT ", "SHOW ")))
        self.assertIn(
            'COPY "public"."users" ("id", "note") TO STDOUT',
            connection.cursor.return_value.copy.call_args_list[0].args[0].as_string(),
        )

    def test_rejects_incomplete_inventory_changed_data_or_sequence_state(self):
        snapshot = parse_dump(DUMP)
        replacements = [
            (0, Mock(fetchone=lambda: ("off",))),
            (1, Mock(fetchall=lambda: [("users",)])),
            (2, Mock(fetchall=lambda: [("id",), ("note",), ("extra",)])),
            (4, Mock(fetchall=lambda: [])),
            (5, Mock(fetchone=lambda: (2, True))),
        ]
        for index, replacement in replacements:
            with self.subTest(index=index):
                connection, values = restored_connection()
                values[index] = replacement
                connection.execute.side_effect = values
                with self.assertRaises(ValueError):
                    verify_restored(snapshot, connection)
        connection, _ = restored_connection()
        connection.cursor.return_value.copy.side_effect = [
            copied([b"b\tchanged\n", b"a\thi\\nthere\n"])
        ]
        with self.assertRaisesRegex(ValueError, "Table content differs"):
            verify_restored(snapshot, connection)

    def test_cli_success_and_errors_never_print_source_rows_or_credentials(self):
        with tempfile.TemporaryDirectory() as temporary, patch.dict(os.environ, {}, clear=True):
            source = Path(temporary) / "data.sql"
            source.write_bytes(DUMP)
            fixture_password = secrets.token_urlsafe(32)
            dsn = make_conninfo(
                host=temporary,
                dbname="neurolab_restore_fixture",
                password=fixture_password,
            )
            connection, _ = restored_connection()
            output = io.StringIO()
            with (
                patch.dict(os.environ, {"RESTORE_DATABASE_URL": dsn}),
                patch(
                    "scripts.verify_postgres_restore.psycopg.connect", return_value=connection
                ) as connect,
                contextlib.redirect_stdout(output),
            ):
                self.assertEqual(main(["--dump-data", str(source)]), 0)
            self.assertIn('"read_only": true', output.getvalue())
            self.assertEqual(connect.call_args.kwargs["options"], READ_ONLY_OPTIONS)
            self.assertNotIn(fixture_password, output.getvalue())
            self.assertNotIn("hi\\nthere", output.getvalue())
            for missing in [False, True]:
                output = io.StringIO()
                filename = str(source) + (".missing" if missing else "")
                with contextlib.redirect_stdout(output):
                    self.assertEqual(main(["--dump-data", filename]), 1)
                self.assertEqual(
                    output.getvalue().strip(),
                    "Restore verification failed; inspect the private operator context.",
                )
            with (
                patch("scripts.verify_postgres_restore.MAX_DATA_BYTES", 1),
                contextlib.redirect_stdout(io.StringIO()),
            ):
                self.assertEqual(main(["--dump-data", str(source)]), 1)


if __name__ == "__main__":
    unittest.main()
