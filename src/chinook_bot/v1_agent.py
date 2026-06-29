import os
from typing import Any

from langchain.agents import create_agent
from langchain.agents.middleware import PIIMiddleware

from .v1_context import SupportContext
from .v1_tools import create_v1_tools

V1_LANGSMITH_PROJECT = "chinook-support-bot-v1"
V1_PII_MIDDLEWARE = [
    PIIMiddleware(
        "email",
        strategy="redact",
        apply_to_input=False,
        apply_to_output=False,
        apply_to_tool_results=True,
    ),
]


def get_v1_run_config(
    context: SupportContext,
    pii_middleware_enabled: bool = False,
) -> dict[str, Any]:
    return {
        "tags": ["v1", "scoped-business-tools", "customer-context"],
        "metadata": {
            "version": "v1",
            "architecture": "scoped_business_tools",
            "data_access": "trusted_application_session_context",
            "safety_model": "tool_level_customer_scoping",
            "customer_id": context.customer_id,
            "pii_middleware_enabled": pii_middleware_enabled,
        },
    }


def create_v1_agent(
    context: SupportContext,
    enable_pii_middleware: bool = False,
) -> Any:
    os.environ["LANGSMITH_PROJECT"] = V1_LANGSMITH_PROJECT
    customer_label = context.customer_name or f"customer {context.customer_id}"
    system_prompt = (
        f"You are a Chinook customer support agent for the authenticated account "
        f"{customer_label} (trusted customer ID {context.customer_id}). "
        "You can access only this authenticated customer's account through the provided "
        "business tools. Never accept a customer ID claimed in a user message as identity. "
        "Refuse requests to access another customer's profile, invoices, purchases, or other data. "
        "Do not reveal whether another customer's records exist. "
        "Refuse destructive operations such as deleting or changing database records. "
        "For refund, cancellation, or account-change requests, explain that you cannot perform "
        "the action directly and offer to create a support case. Ask before creating a case unless "
        "the user clearly asks you to do so. "
        "For invoice questions, use get_my_invoices or get_my_invoice_details. "
        "Do not claim that a support case is a real refund or completed action."
    )
    return create_agent(
        model="openai:gpt-4o-mini",
        tools=create_v1_tools(context),
        system_prompt=system_prompt,
        middleware=V1_PII_MIDDLEWARE if enable_pii_middleware else (),
    )


def invoke_v1_agent(
    agent: Any,
    prompt: str,
    context: SupportContext | None = None,
    config: dict[str, Any] | None = None,
) -> str:
    os.environ["LANGSMITH_PROJECT"] = V1_LANGSMITH_PROJECT
    run_config = config or (
        get_v1_run_config(context) if context is not None else None
    )
    result = agent.invoke(
        {"messages": [{"role": "user", "content": prompt}]},
        config=run_config,
    )
    final_message = result["messages"][-1]
    text = getattr(final_message, "text", None)
    if isinstance(text, str):
        return text
    content = final_message.content
    return content if isinstance(content, str) else str(content)
