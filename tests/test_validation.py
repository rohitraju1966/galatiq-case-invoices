"""Tests for the deterministic validation node, the money/correctness core."""

from __future__ import annotations

from agents.nodes.validation import validate_invoice
from agents.tools.db import InvoiceDB
from schemas import InvoiceExtraction, LineItem


def _line(item: str, qty: int, price: float, line_total: float | None = None) -> dict:
    return {
        "item_name": item,
        "quantity": qty,
        "unit_price": price,
        "line_total": line_total if line_total is not None else qty * price,
    }


def _state(
    line_items: list[dict],
    *,
    invoice_number: str = "INV-T",
    merchant: str = "Atlas Industrial Supply",
    currency: str = "USD",
    trn_id: int = 1,
    tax: float = 0.0,
    subtotal: float | None = None,
    total: float | None = None,
) -> dict:
    sub = (
        subtotal if subtotal is not None else sum(li["line_total"] for li in line_items)
    )
    tot = total if total is not None else sub + tax
    return {
        "invoice_data": {
            "invoice_number": invoice_number,
            "merchant_name": merchant,
            "currency": currency,
            "subtotal": sub,
            "tax": tax,
            "total": tot,
        },
        "line_items": line_items,
        "trn_id": trn_id,
    }


def _flag_prefixes(result: dict) -> set[str]:
    return {flag.split(":")[0] for flag in result["validation_flags"]}


def _approve_prior(invoice_number: str, items: list[tuple[str, int, float]]) -> int:
    db = InvoiceDB()
    data = InvoiceExtraction(
        invoice_number=invoice_number,
        merchant_name="Atlas Industrial Supply",
        invoice_date=None,
        due_date=None,
        subtotal=sum(q * p for _, q, p in items),
        tax=0.0,
        total=sum(q * p for _, q, p in items),
        currency="USD",
        line_items=[
            LineItem(item_name=n, quantity=q, unit_price=p, line_total=q * p)
            for n, q, p in items
        ],
    )
    trn_id = db.insert_invoice(data, "test")
    db.insert_line_items(trn_id, data)
    db.log_audit(trn_id, "approved", "approved for test", "vp_agent")
    return trn_id


def test_validate_invoice_clean_has_no_flags(seeded_db):
    result = validate_invoice(_state([_line("WidgetA", 2, 250.0)]))
    assert result["status"] == "validated"
    assert result["validation_flags"] == []


def test_validate_invoice_flags_stock_exceeded(seeded_db):
    result = validate_invoice(_state([_line("GadgetX", 20, 750.0)]))
    assert "stock_exceeded" in _flag_prefixes(result)


def test_validate_invoice_flags_unknown_item(seeded_db):
    result = validate_invoice(_state([_line("FakeItem", 1, 100.0)]))
    assert "unknown_item" in _flag_prefixes(result)


def test_validate_invoice_flags_negative_quantity(seeded_db):
    result = validate_invoice(_state([_line("WidgetA", -2, 250.0)]))
    assert "negative_value" in _flag_prefixes(result)


def test_validate_invoice_flags_unknown_merchant(seeded_db):
    result = validate_invoice(
        _state([_line("WidgetA", 1, 250.0)], merchant="Fraudster LLC")
    )
    assert "unknown_merchant" in _flag_prefixes(result)


def test_validate_invoice_flags_line_math_error(seeded_db):
    result = validate_invoice(_state([_line("WidgetA", 2, 250.0, line_total=600.0)]))
    assert "line_math_error" in _flag_prefixes(result)


def test_validate_invoice_flags_foreign_currency(seeded_db):
    result = validate_invoice(_state([_line("WidgetA", 1, 250.0)], currency="EUR"))
    assert "foreign_currency" in _flag_prefixes(result)


def test_validate_invoice_rejects_duplicate_after_approval(seeded_db):
    _approve_prior("INV-DUP", [("WidgetA", 1, 250.0)])
    result = validate_invoice(
        _state([_line("WidgetA", 1, 250.0)], invoice_number="INV-DUP", trn_id=999)
    )
    assert result["status"] == "rejected"
    assert "duplicate_invoice" in result["validation_flags"]


def test_validate_invoice_stock_is_cumulative_across_invoices(seeded_db):
    _approve_prior("INV-PRIOR", [("WidgetA", 10, 250.0)])
    result = validate_invoice(
        _state([_line("WidgetA", 8, 250.0)], invoice_number="INV-NEW", trn_id=999)
    )
    assert "stock_exceeded" in _flag_prefixes(result)


def test_validate_invoice_no_line_total_is_not_a_math_error(seeded_db):
    line = {
        "item_name": "WidgetA",
        "quantity": 14,
        "unit_price": 250.0,
        "line_total": None,
    }
    result = validate_invoice(_state([line], subtotal=3500.0))
    assert result["validation_flags"] == []
