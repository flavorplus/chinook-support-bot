import re
from typing import Any, Optional
from langchain_core.tools import Tool
from .db import get_connection, list_tables, get_schema_and_samples, run_query

BLOCKED_KEYWORDS = [
    "INSERT",
    "UPDATE",
    "DELETE",
    "DROP",
    "ALTER",
    "CREATE",
    "REPLACE",
    "TRUNCATE",
]


def _format_table_result(result: dict[str, Any]) -> str:
    lines: list[str] = []
    if not result["columns"]:
        return "No results returned."
    lines.append("Columns: " + ", ".join(result["columns"]))
    lines.append("Rows:")
    for row in result["rows"]:
        lines.append(str(row))
    return "\n".join(lines)


def _list_tables(_: str) -> str:
    tables = list_tables(get_connection())
    if not tables:
        return "No tables found."
    return "Available tables: " + ", ".join(tables)


def _schema(query: str) -> str:
    table_names = [name.strip() for name in query.split(",") if name.strip()]
    if not table_names:
        table_names = list_tables(get_connection())
    schema_info = get_schema_and_samples(table_names)
    pieces: list[str] = []
    for table_name, payload in schema_info.items():
        pieces.append(f"Table: {table_name}")
        pieces.append(payload.get("ddl", ""))
        pieces.append("Columns: " + ", ".join(payload.get("columns", [])))
        samples = payload.get("samples", [])
        if samples:
            pieces.append("Sample rows:")
            for sample in samples:
                pieces.append(str(sample))
        pieces.append("---")
    return "\n".join(pieces).strip()


def _query_checker(query: str) -> str:
    for keyword in BLOCKED_KEYWORDS:
        if re.search(rf"\b{keyword}\b", query, re.IGNORECASE):
            return f"Query blocked: destructive SQL keyword found ({keyword})."
    return "Query appears safe."


def _query_runner(query: str, db_path: Optional[str] = None) -> str:
    checker = _query_checker(query)
    if checker.startswith("Query blocked"):
        return checker
    try:
        result = run_query(query, db_path=db_path)
        return _format_table_result(result)
    except Exception as exc:
        return f"Error executing query: {exc}"


def sql_db_list_tables() -> Tool:
    return Tool(
        name="sql_db_list_tables",
        func=_list_tables,
        description="List the tables available in the Chinook SQL database.",
    )


def sql_db_schema() -> Tool:
    return Tool(
        name="sql_db_schema",
        func=_schema,
        description="Return schema and sample rows for one or more Chinook tables. Use a comma-separated table list or leave blank for all tables.",
    )


def sql_db_query_checker() -> Tool:
    return Tool(
        name="sql_db_query_checker",
        func=_query_checker,
        description="Check a SQL query for destructive statements before executing it.",
    )


def sql_db_query(db_path: Optional[str] = None) -> Tool:
    return Tool(
        name="sql_db_query",
        func=lambda query: _query_runner(query, db_path=db_path),
        description="Execute a safe SQL query against the Chinook database and return formatted results.",
    )
