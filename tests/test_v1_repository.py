from chinook_bot.v1_repository import (
    get_customer_invoices,
    get_customer_profile,
    get_invoice_for_customer,
    get_purchased_tracks_for_customer,
    get_recommendations_for_customer,
)


def test_get_customer_profile_returns_customer_5() -> None:
    profile = get_customer_profile(5)
    assert profile is not None
    assert profile["CustomerId"] == 5


def test_get_customer_invoices_returns_customer_5_invoices() -> None:
    invoices = get_customer_invoices(5)
    assert invoices
    assert all(invoice["CustomerId"] == 5 for invoice in invoices)


def test_get_invoice_for_customer_returns_owned_invoice() -> None:
    invoice = get_invoice_for_customer(5, 306)
    assert invoice is not None
    assert invoice["InvoiceId"] == 306
    assert invoice["CustomerId"] == 5


def test_get_invoice_for_customer_rejects_other_customer() -> None:
    assert get_invoice_for_customer(3, 306) is None


def test_get_purchased_tracks_returns_a_list() -> None:
    tracks = get_purchased_tracks_for_customer(5)
    assert isinstance(tracks, list)
    assert tracks


def test_get_recommendations_returns_a_list() -> None:
    recommendations = get_recommendations_for_customer(5)
    assert isinstance(recommendations, list)
