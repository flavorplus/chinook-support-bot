from langchain_core.tools import tool

from .v1_context import SupportContext
from .v1_repository import (
    create_mock_support_case,
    get_customer_invoices,
    get_customer_profile,
    get_invoice_for_customer,
    get_invoice_lines_for_customer,
    get_purchased_tracks_for_customer,
    get_recommendations_for_customer,
)


def create_v1_tools(context: SupportContext) -> list:
    customer_id = context.customer_id

    @tool
    def get_my_profile() -> dict | None:
        """Get the authenticated customer's profile."""
        return get_customer_profile(customer_id)

    @tool
    def get_my_invoices() -> list[dict]:
        """List invoices belonging to the authenticated customer."""
        return get_customer_invoices(customer_id)

    @tool
    def get_my_invoice_details(invoice_id: int) -> dict:
        """Get one invoice and its line items for the authenticated customer."""
        invoice = get_invoice_for_customer(customer_id, invoice_id)
        if invoice is None:
            return {"found": False, "message": "Invoice not found for this account."}
        return {
            "found": True,
            "invoice": invoice,
            "lines": get_invoice_lines_for_customer(customer_id, invoice_id),
        }

    @tool
    def get_my_purchased_tracks(limit: int = 20) -> list[dict]:
        """List tracks purchased by the authenticated customer."""
        return get_purchased_tracks_for_customer(customer_id, limit)

    @tool
    def recommend_music_for_me(limit: int = 5) -> list[dict]:
        """Recommend unpurchased music based on the authenticated customer's purchases."""
        return get_recommendations_for_customer(customer_id, limit)

    @tool
    def create_support_case(reason: str, invoice_id: int | None = None) -> dict:
        """Create a mock support case for the authenticated customer."""
        return create_mock_support_case(customer_id, reason, invoice_id)

    return [
        get_my_profile,
        get_my_invoices,
        get_my_invoice_details,
        get_my_purchased_tracks,
        recommend_music_for_me,
        create_support_case,
    ]
