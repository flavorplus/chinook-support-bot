import os
from pathlib import Path
from typing import Any, Optional

from langchain.agents import create_agent

from .v0_tools import sql_db_list_tables, sql_db_schema, sql_db_query_checker, sql_db_query

V0_LANGSMITH_PROJECT = "chinook-support-bot-v0"
V0_RUN_CONFIG = {
    "tags": ["v0", "generic-sql-agent", "baseline"],
    "metadata": {
        "version": "v0",
        "architecture": "generic_sql_agent",
        "data_access": "generic_sql_tools",
        "safety_model": "prompt_and_basic_sql_blocking",
    },
}


def create_v0_agent(db_path: Optional[str] = None) -> Any:
    os.environ["LANGSMITH_PROJECT"] = V0_LANGSMITH_PROJECT
    if db_path is None:
        db_path = str(Path(__file__).resolve().parents[2] / "data" / "Chinook.db")

    tools = [
        sql_db_list_tables(),
        sql_db_schema(),
        sql_db_query_checker(),
        sql_db_query(db_path=db_path),
    ]

    system_prompt = (
        "You are a Chinook support agent. Inspect the database tables and schema before querying. "
        "Check SQL queries for destructive statements before executing them. "
        "Avoid broad result sets and answer using the Chinook database. "
        "If a user asks for actions like refunds, explain that you cannot perform real refunds and provide data only."
    )

    return create_agent(
        model="openai:gpt-4o-mini",
        tools=tools,
        system_prompt=system_prompt,
    )


def invoke_v0_agent(
    agent: Any,
    prompt: str,
    config: dict[str, Any] | None = None,
) -> str:
    os.environ["LANGSMITH_PROJECT"] = V0_LANGSMITH_PROJECT
    result = agent.invoke(
        {"messages": [{"role": "user", "content": prompt}]},
        config=config or V0_RUN_CONFIG,
    )
    final_message = result["messages"][-1]
    text = getattr(final_message, "text", None)
    if isinstance(text, str):
        return text
    content = final_message.content
    return content if isinstance(content, str) else str(content)
