"""Translate the pipeline's internal vocabulary into plain language for a
non-technical finance reader."""

from __future__ import annotations

import re
from dataclasses import dataclass

from typing import Callable


@dataclass
class FriendlyFlag:
    title: str
    detail: str
    severity: str  


@dataclass
class StatusBadge:
    label: str
    tone: str  


def _money(val: float) -> str:
    return f"${val:,.0f}" if float(val).is_integer() else f"${val:,.2f}"


def _num(val: str) -> float:
    try:
        return float(val)
    except ValueError:
        return 0.0


def _kv(text: str) -> dict[str, str]:
    return dict(re.findall(r"([\w+]+)=([\-\d.]+)", text))


def _item_name(rest: str) -> str:
    return rest.split("(")[0].strip()


def _price_mismatch(rest: str) -> FriendlyFlag:
    item = _item_name(rest)
    kv = _kv(rest)
    invoice, master = _num(kv.get("invoice", "0")), _num(kv.get("master", "0"))
    over = invoice - master
    direction = "over" if over > 0 else "under"
    return FriendlyFlag(
        "Price differs from agreed",
        f"{item} billed at {_money(invoice)}/unit versus our agreed {_money(master)}/unit "
        f"({_money(abs(over))} {direction} per unit).",
        "warning",
    )


def _stock_exceeded(rest: str) -> FriendlyFlag:
    item = _item_name(rest)
    kv = _kv(rest)
    approved, invoice, stock = _num(kv.get("approved", "0")), _num(kv.get("invoice", "0")), _num(kv.get("stock", "0"))
    already = f" on top of {int(approved)} already approved this year" if approved else ""
    return FriendlyFlag(
        "Order larger than available stock",
        f"{item}: this invoice orders {int(invoice)} unit(s){already}, but only {int(stock)} are in stock.",
        "warning",
    )


def _budget_exceeded(rest: str) -> FriendlyFlag:
    item = _item_name(rest)
    kv = _kv(rest)
    approved, invoice, budget = _num(kv.get("approved", "0")), _num(kv.get("invoice", "0")), _num(kv.get("budget", "0"))
    already = f" plus {_money(approved)} already approved" if approved else ""
    return FriendlyFlag(
        "Exceeds remaining budget",
        f"{item}: this invoice ({_money(invoice)}){already} would go over the {_money(budget)} budget for this item.",
        "warning",
    )


def _line_math(rest: str) -> FriendlyFlag:
    return FriendlyFlag(
        "The numbers don't add up",
        f"{_item_name(rest)}: quantity times unit price doesn't match the line total shown on the invoice.",
        "danger",
    )


def _subtotal_mismatch(rest: str) -> FriendlyFlag:
    kv = _kv(rest)
    return FriendlyFlag(
        "Subtotal doesn't match the items",
        f"The line items add up to {_money(_num(kv.get('sum', '0')))}, "
        f"but the invoice subtotal says {_money(_num(kv.get('subtotal', '0')))}.",
        "danger",
    )


def _total_mismatch(rest: str) -> FriendlyFlag:
    kv = _kv(rest)
    return FriendlyFlag(
        "Total doesn't add up",
        f"Subtotal plus tax comes to {_money(_num(kv.get('subtotal+tax', '0')))}, "
        f"but the invoice total says {_money(_num(kv.get('total', '0')))}.",
        "danger",
    )


def _unknown_item(rest: str) -> FriendlyFlag:
    return FriendlyFlag(
        "Item not in our catalog",
        f"“{rest}” isn't on our product list — it may be mislabelled or unrecognised.",
        "danger",
    )


def _unknown_merchant(rest: str) -> FriendlyFlag:
    return FriendlyFlag(
        "Supplier not approved",
        f"“{rest}” isn't on our approved supplier list.",
        "danger",
    )


def _normalized_match(rest: str) -> FriendlyFlag:
    parts = rest.split("->")
    shown = parts[0].strip()
    matched = parts[1].strip() if len(parts) > 1 else ""
    return FriendlyFlag(
        "Matched with a minor name difference",
        f"Invoice says “{shown}”; we matched it to {matched} in our catalog.",
        "info",
    )


def _negative_value(rest: str) -> FriendlyFlag:
    return FriendlyFlag("Invalid amount", f"{rest}: contains a negative quantity or price.", "danger")


def _foreign_currency(rest: str) -> FriendlyFlag:
    currency = rest.split()[0] if rest else "a foreign currency"
    return FriendlyFlag(
        "Foreign currency",
        f"This invoice is in {currency}. We couldn't verify the amounts against our USD price list.",
        "warning",
    )


def _missing_merchant(_rest: str) -> FriendlyFlag:
    return FriendlyFlag("No supplier name", "The invoice doesn't list a supplier.", "danger")


def _negative_total(_rest: str) -> FriendlyFlag:
    return FriendlyFlag("Invalid total", "The invoice total is a negative amount.", "danger")


def _duplicate(_rest: str) -> FriendlyFlag:
    return FriendlyFlag(
        "Possible duplicate",
        "We've already processed and approved an invoice with this number.",
        "danger",
    )


_FLAG_HANDLERS: dict[str, Callable[[str], FriendlyFlag]] = {
    "price_mismatch": _price_mismatch,
    "stock_exceeded": _stock_exceeded,
    "budget_exceeded": _budget_exceeded,
    "line_math_error": _line_math,
    "subtotal_mismatch": _subtotal_mismatch,
    "total_mismatch": _total_mismatch,
    "unknown_item": _unknown_item,
    "unknown_merchant": _unknown_merchant,
    "normalized_match": _normalized_match,
    "negative_value": _negative_value,
    "foreign_currency": _foreign_currency,
    "missing_merchant": _missing_merchant,
    "negative_total": _negative_total,
    "duplicate_invoice": _duplicate,
}


def humanize_flag(flag: str) -> FriendlyFlag:
    prefix, _, rest = flag.partition(": ")
    handler = _FLAG_HANDLERS.get(prefix)
    if handler:
        return handler(rest)
    return FriendlyFlag(prefix.replace("_", " ").capitalize(), rest, "warning")


def parse_flags(review_note: str) -> list[FriendlyFlag]:
    if not review_note or review_note.strip() == "All checks passed":
        return []
    return [humanize_flag(part.strip()) for part in review_note.split(" | ") if part.strip()]


_REVIEWER_NAMES: dict[str, str] = {
    "extraction_agent": "Reading the invoice",
    "validation": "Automated checks",
    "vp_agent": "VP of Finance",
    "auditor_agent": "Senior Auditor",
    "graph": "System",
    "payment": "Payment",
}


def reviewer_name(reviewed_by: str) -> str:
    return _REVIEWER_NAMES.get(reviewed_by, reviewed_by.replace("_", " ").title())


_STATUS_BADGES: dict[str, tuple[str, str]] = {
    "extracted": ("Read", "accent"),
    "validated": ("Checked", "accent"),
    "approved": ("Approved", "success"),
    "rejected": ("Rejected", "danger"),
    "paid": ("Paid", "success"),
    "auditor_review": ("Escalated for senior review", "warning"),
    "auditor_reviewed": ("Senior review complete", "accent"),
    "fx_review_hold": ("On hold — foreign currency", "warning"),
    "vp_review_required": ("Awaiting VP", "accent"),
}


def status_badge(status: str) -> StatusBadge:
    label, tone = _STATUS_BADGES.get(status, (status.replace("_", " ").capitalize(), "neutral"))
    return StatusBadge(label, tone)
