from langchain.agents.middleware import PIIMiddleware

from chinook_bot.v1_agent import V1_PII_MIDDLEWARE, get_v1_run_config
from chinook_bot.v1_context import SupportContext
from chinook_bot.v1_repository import get_invoice_for_customer
from chinook_bot.v1_tools import create_v1_tools


def test_customer_3_cannot_access_customer_5_invoice() -> None:
    assert get_invoice_for_customer(3, 306) is None


def test_customer_5_cannot_access_another_customers_invoice() -> None:
    assert get_invoice_for_customer(5, 1) is None


def test_v1_tools_do_not_accept_customer_id() -> None:
    tools = create_v1_tools(SupportContext(customer_id=5))
    assert {tool.name for tool in tools} == {
        "get_my_profile",
        "get_my_invoices",
        "get_my_invoice_details",
        "get_my_purchased_tracks",
        "recommend_music_for_me",
        "create_support_case",
    }
    for tool in tools:
        assert "customer_id" not in tool.args


def test_invoice_tool_cannot_return_cross_customer_invoice() -> None:
    tools = {
        tool.name: tool
        for tool in create_v1_tools(SupportContext(customer_id=5))
    }
    result = tools["get_my_invoice_details"].invoke({"invoice_id": 1})
    assert result == {
        "found": False,
        "message": "Invoice not found for this account.",
    }


def test_v1_uses_pii_middleware_for_model_boundaries() -> None:
    assert all(isinstance(item, PIIMiddleware) for item in V1_PII_MIDDLEWARE)
    assert [item.pii_type for item in V1_PII_MIDDLEWARE] == ["email"]
    assert all(not item.apply_to_input for item in V1_PII_MIDDLEWARE)
    assert all(not item.apply_to_output for item in V1_PII_MIDDLEWARE)
    assert all(item.apply_to_tool_results for item in V1_PII_MIDDLEWARE)


def test_v1_run_config_records_optional_pii_middleware() -> None:
    context = SupportContext(customer_id=5)
    assert get_v1_run_config(context)["metadata"]["pii_middleware_enabled"] is False
    assert (
        get_v1_run_config(
            context,
            pii_middleware_enabled=True,
        )["metadata"]["pii_middleware_enabled"]
        is True
    )
