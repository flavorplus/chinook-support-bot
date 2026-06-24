from contextlib import closing
from typing import Any
from uuid import uuid4

from .db import get_connection


def _row_to_dict(row: Any) -> dict[str, Any] | None:
    return dict(row) if row is not None else None


def get_customer_profile(customer_id: int) -> dict | None:
    with closing(get_connection()) as conn:
        row = conn.execute(
            """
            SELECT CustomerId, FirstName, LastName, Company, Address, City, State,
                   Country, PostalCode, Phone, Email
            FROM Customer
            WHERE CustomerId = ?
            """,
            (customer_id,),
        ).fetchone()
    return _row_to_dict(row)


def get_customer_invoices(customer_id: int) -> list[dict]:
    with closing(get_connection()) as conn:
        rows = conn.execute(
            """
            SELECT InvoiceId, CustomerId, InvoiceDate, BillingAddress, BillingCity,
                   BillingState, BillingCountry, BillingPostalCode, Total
            FROM Invoice
            WHERE CustomerId = ?
            ORDER BY InvoiceDate DESC, InvoiceId DESC
            """,
            (customer_id,),
        ).fetchall()
    return [dict(row) for row in rows]


def get_invoice_for_customer(customer_id: int, invoice_id: int) -> dict | None:
    with closing(get_connection()) as conn:
        row = conn.execute(
            """
            SELECT InvoiceId, CustomerId, InvoiceDate, BillingAddress, BillingCity,
                   BillingState, BillingCountry, BillingPostalCode, Total
            FROM Invoice
            WHERE CustomerId = ? AND InvoiceId = ?
            """,
            (customer_id, invoice_id),
        ).fetchone()
    return _row_to_dict(row)


def get_invoice_lines_for_customer(customer_id: int, invoice_id: int) -> list[dict]:
    with closing(get_connection()) as conn:
        rows = conn.execute(
            """
            SELECT il.InvoiceLineId, il.InvoiceId, il.TrackId, t.Name AS TrackName,
                   ar.Name AS ArtistName, al.Title AS AlbumTitle, g.Name AS Genre,
                   il.UnitPrice, il.Quantity
            FROM InvoiceLine AS il
            JOIN Invoice AS i ON i.InvoiceId = il.InvoiceId
            JOIN Track AS t ON t.TrackId = il.TrackId
            LEFT JOIN Album AS al ON al.AlbumId = t.AlbumId
            LEFT JOIN Artist AS ar ON ar.ArtistId = al.ArtistId
            LEFT JOIN Genre AS g ON g.GenreId = t.GenreId
            WHERE i.CustomerId = ? AND i.InvoiceId = ?
            ORDER BY il.InvoiceLineId
            """,
            (customer_id, invoice_id),
        ).fetchall()
    return [dict(row) for row in rows]


def get_purchased_tracks_for_customer(customer_id: int, limit: int = 20) -> list[dict]:
    with closing(get_connection()) as conn:
        rows = conn.execute(
            """
            SELECT t.TrackId, t.Name AS TrackName, ar.Name AS ArtistName,
                   al.Title AS AlbumTitle, g.Name AS Genre,
                   SUM(il.Quantity) AS QuantityPurchased
            FROM Invoice AS i
            JOIN InvoiceLine AS il ON il.InvoiceId = i.InvoiceId
            JOIN Track AS t ON t.TrackId = il.TrackId
            LEFT JOIN Album AS al ON al.AlbumId = t.AlbumId
            LEFT JOIN Artist AS ar ON ar.ArtistId = al.ArtistId
            LEFT JOIN Genre AS g ON g.GenreId = t.GenreId
            WHERE i.CustomerId = ?
            GROUP BY t.TrackId, t.Name, ar.Name, al.Title, g.Name
            ORDER BY QuantityPurchased DESC, t.Name
            LIMIT ?
            """,
            (customer_id, max(0, limit)),
        ).fetchall()
    return [dict(row) for row in rows]


def get_recommendations_for_customer(customer_id: int, limit: int = 5) -> list[dict]:
    with closing(get_connection()) as conn:
        rows = conn.execute(
            """
            WITH FavoriteGenres AS (
                SELECT t.GenreId, SUM(il.Quantity) AS PurchaseCount
                FROM Invoice AS i
                JOIN InvoiceLine AS il ON il.InvoiceId = i.InvoiceId
                JOIN Track AS t ON t.TrackId = il.TrackId
                WHERE i.CustomerId = ? AND t.GenreId IS NOT NULL
                GROUP BY t.GenreId
                ORDER BY PurchaseCount DESC
                LIMIT 3
            ),
            PurchasedTracks AS (
                SELECT DISTINCT il.TrackId
                FROM Invoice AS i
                JOIN InvoiceLine AS il ON il.InvoiceId = i.InvoiceId
                WHERE i.CustomerId = ?
            )
            SELECT t.TrackId, t.Name AS TrackName, ar.Name AS ArtistName,
                   al.Title AS AlbumTitle, g.Name AS Genre
            FROM Track AS t
            JOIN FavoriteGenres AS fg ON fg.GenreId = t.GenreId
            LEFT JOIN Album AS al ON al.AlbumId = t.AlbumId
            LEFT JOIN Artist AS ar ON ar.ArtistId = al.ArtistId
            LEFT JOIN Genre AS g ON g.GenreId = t.GenreId
            LEFT JOIN PurchasedTracks AS pt ON pt.TrackId = t.TrackId
            WHERE pt.TrackId IS NULL
            ORDER BY fg.PurchaseCount DESC, ar.Name, al.Title, t.Name
            LIMIT ?
            """,
            (customer_id, customer_id, max(0, limit)),
        ).fetchall()
    return [dict(row) for row in rows]


def create_mock_support_case(
    customer_id: int,
    reason: str,
    invoice_id: int | None = None,
) -> dict:
    if get_customer_profile(customer_id) is None:
        return {"created": False, "error": "Authenticated customer was not found."}
    if invoice_id is not None and get_invoice_for_customer(customer_id, invoice_id) is None:
        return {
            "created": False,
            "error": "Invoice was not found for the authenticated customer.",
        }
    return {
        "created": True,
        "case_id": f"CASE-{uuid4().hex[:8].upper()}",
        "customer_id": customer_id,
        "invoice_id": invoice_id,
        "reason": reason,
        "status": "open",
        "mock": True,
    }
