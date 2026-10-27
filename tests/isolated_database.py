"""Disposable SQLite or explicitly named local PostgreSQL test schema."""

import os
import uuid
from contextlib import contextmanager
from pathlib import Path
from urllib.parse import parse_qsl, quote, urlencode, urlsplit


@contextmanager
def isolated_database(directory):
    base = os.getenv("NEUROLAB_TEST_POSTGRES_URL")
    if not base:
        yield str(Path(directory) / "test.db")
        return
    import psycopg
    from psycopg import sql
    from psycopg.conninfo import conninfo_to_dict

    if not conninfo_to_dict(base)["dbname"].startswith("neurolab_job_test_"):
        raise ValueError("Tests require an explicitly disposable PostgreSQL database")
    schema = "test_" + uuid.uuid4().hex
    with psycopg.connect(base, autocommit=True) as connection:
        connection.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(schema)))
    url = urlsplit(base)
    query = dict(parse_qsl(url.query))
    query["options"] = "-c search_path=" + schema
    path = f"{url.scheme}://{url.netloc}{url.path}?{urlencode(query, quote_via=quote)}"
    try:
        yield path
    finally:
        with psycopg.connect(base, autocommit=True) as connection:
            connection.execute(sql.SQL("DROP SCHEMA {} CASCADE").format(sql.Identifier(schema)))
