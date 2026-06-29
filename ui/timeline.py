"""Reconstruct a render-ready story of one invoice from the audit log."""

from __future__ import annotations

from dataclasses import dataclass, field

from agents.tools.db import InvoiceDB
from ui.humanize import (
    FriendlyFlag,
    StatusBadge,
    parse_flags,
    reviewer_name,
    status_badge,
)


@dataclass
class TimelineStep:
    key: str
    title: str
    reviewer: str
    note: str
    badge: StatusBadge | None = None
    flags: list[FriendlyFlag] = field(default_factory=list)
    nested: bool = False


@dataclass
class InvoiceSummary:
    trn_id: int
    invoice_number: str
    merchant_name: str
    total: float | None
    currency: str
    due_date: str
    source_file: str
    item_count: int


@dataclass
class Timeline:
    summary: InvoiceSummary | None
    steps: list[TimelineStep]
    final_status: str


_STAGE_TITLES = {
    "extraction": "Reading the invoice",
    "validation": "Checking the invoice",
    "escalation": "Escalated for senior review",
    "auditor": "Senior auditor's review",
    "payment": "Payment",
}


def _extraction_step(reviewed_by: str) -> TimelineStep:
    return TimelineStep(
        "extraction",
        _STAGE_TITLES["extraction"],
        reviewer_name(reviewed_by),
        "We read the invoice and pulled out the supplier, dates, items, and totals.",
    )


def _validation_step(status: str, note: str, reviewed_by: str) -> TimelineStep:
    if status == "rejected":
        return TimelineStep(
            "validation",
            _STAGE_TITLES["validation"],
            reviewer_name(reviewed_by),
            "We stopped here — this invoice failed a basic check.",
            badge=status_badge("rejected"),
            flags=parse_flags(note) or [],
        )
    flags = parse_flags(note)
    if not flags:
        summary = "We ran our standard checks and everything looks right."
    else:
        summary = (
            f"We ran our standard checks and found {len(flags)} thing(s) worth a look."
        )
    return TimelineStep(
        "validation",
        _STAGE_TITLES["validation"],
        reviewer_name(reviewed_by),
        summary,
        flags=flags,
    )


def _escalation_step() -> TimelineStep:
    return TimelineStep(
        "escalation",
        _STAGE_TITLES["escalation"],
        reviewer_name("graph"),
        "This invoice is above the $10,000 threshold, so a senior auditor independently "
        "reviews it before the final decision.",
    )


def _auditor_step(note: str, reviewed_by: str) -> TimelineStep:
    return TimelineStep(
        "auditor",
        _STAGE_TITLES["auditor"],
        reviewer_name(reviewed_by),
        note,
        nested=True,
    )


def _vp_step(status: str, note: str, reviewed_by: str, is_final: bool) -> TimelineStep:
    return TimelineStep(
        "vp_final" if is_final else "vp_initial",
        "VP's final decision" if is_final else "VP's initial review",
        reviewer_name(reviewed_by),
        note,
        badge=status_badge(status),
    )


def _payment_step(note: str, reviewed_by: str) -> TimelineStep:
    return TimelineStep(
        "payment",
        _STAGE_TITLES["payment"],
        reviewer_name(reviewed_by),
        note,
        badge=status_badge("paid"),
    )


def _build_summary(db: InvoiceDB, trn_id: int) -> InvoiceSummary | None:
    invoice = db.get_invoice(trn_id)
    if invoice is None:
        return None
    return InvoiceSummary(
        trn_id=trn_id,
        invoice_number=str(invoice.invoice_number),
        merchant_name=str(invoice.merchant_name)
        if invoice.merchant_name
        else "Unknown supplier",
        total=invoice.total,
        currency=str(invoice.currency) if invoice.currency else "USD",
        due_date=str(invoice.due_date) if invoice.due_date else "—",
        source_file=str(invoice.source_file) if invoice.source_file else "",
        item_count=len(db.get_items(trn_id)),
    )


def build_timeline(db: InvoiceDB, trn_id: int) -> Timeline:
    rows = db.get_audit_trail(trn_id)
    vp_total = sum(1 for r in rows if r.reviewed_by == "vp_agent")

    steps: list[TimelineStep] = []
    vp_seen = 0
    final_status = "extracted"

    for row in rows:
        status = str(row.status)
        note = str(row.review_note)
        reviewed_by = str(row.reviewed_by)
        final_status = status

        if status == "extracted":
            steps.append(_extraction_step(reviewed_by))
        elif reviewed_by == "validation":
            steps.append(_validation_step(status, note, reviewed_by))
        elif reviewed_by == "graph" and status == "auditor_review":
            steps.append(_escalation_step())
        elif reviewed_by == "auditor_agent":
            steps.append(_auditor_step(note, reviewed_by))
        elif reviewed_by == "vp_agent":
            vp_seen += 1
            steps.append(
                _vp_step(status, note, reviewed_by, is_final=(vp_seen == vp_total))
            )
        elif reviewed_by == "payment":
            steps.append(_payment_step(note, reviewed_by))

    return Timeline(
        summary=_build_summary(db, trn_id),
        steps=steps,
        final_status=final_status,
    )
