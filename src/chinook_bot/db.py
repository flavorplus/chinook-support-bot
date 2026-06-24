import sqlite3
import pathlib
from typing import Any, Optional

ROOT_DIR = pathlib.Path(__file__).resolve().parents[2]
DB_PATH = ROOT_DIR / "data" / "Chinook.db"


def get_connection(db_path: Optional[str] = None) -> sqlite3.Connection:
    path = DB_PATH if db_path is None else pathlib.Path(db_path)
    conn = sqlite3.connect(path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def list_tables(conn: Optional[sqlite3.Connection] = None) -> list[str]:
    close_conn = False
    if conn is None:
        conn = get_connection()
        close_conn = True
    cursor = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';"
    )
    rows = [row[0] for row in cursor.fetchall()]
    if close_conn:
        conn.close()
    return rows


def get_schema_and_samples(table_names: list[str], sample_limit: int = 3) -> dict[str, Any]:
    conn = get_connection()
    result: dict[str, Any] = {}
    for table_name in table_names:
        cursor = conn.execute(
            "SELECT sql FROM sqlite_master WHERE type='table' AND name=?;",
            (table_name,),
        )
        row = cursor.fetchone()
        ddl = row[0] if row else ""
        sample_rows = []
        columns: list[str] = []
        try:
            query = f"SELECT * FROM {table_name} LIMIT ?"
            sample_cursor = conn.execute(query, (sample_limit,))
            columns = [col[0] for col in sample_cursor.description] if sample_cursor.description else []
            sample_rows = [dict(row) for row in sample_cursor.fetchall()]
        except sqlite3.Error:
            pass
        result[table_name] = {
            "ddl": ddl,
            "columns": columns,
            "samples": sample_rows,
        }
    conn.close()
    return result


def run_query(query: str, db_path: Optional[str] = None) -> dict[str, Any]:
    conn = get_connection(db_path)
    cursor = conn.execute(query)
    columns = [col[0] for col in cursor.description] if cursor.description else []
    rows = [tuple(row) for row in cursor.fetchall()]
    conn.close()
    return {"columns": columns, "rows": rows}
