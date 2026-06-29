"""Aggregate all processed invoices into summary stats for the Dashboard tab."""

from __future__ import annotations

from dataclasses import dataclass, field

from agents.tools.db import InvoiceDB

RECENT_LIMIT = 10

_OUTCOME = {
    "paid": ("Paid", "success"),
    "approved": ("Approved", "success"),
    "rejected": ("Rejected", "danger"),
    "fx_review_hold": ("Held", "warning"),
    "auditor_review": ("In review", "accent"),
}


@dataclass
class RecentRow:
    invoice_number: str
    merchant: str
    total: float | None
    status_label: str
    tone: str


@dataclass
class DashboardData:
    processed: int = 0
    total_paid: float = 0.0
    approval_rate: int = 0
    needs_attention: int = 0
    outcomes: dict[str, int] = field(default_factory=dict)
    recent: list[RecentRow] = field(default_factory=list)


def _final_status(db: InvoiceDB, trn_id: int) -> str:
    rows = db.get_audit_trail(trn_id)
    return str(rows[-1].status) if rows else "extracted"


def load_dashboard(db: InvoiceDB) -> DashboardData:
    invoices = db.list_invoices()
    data = DashboardData(processed=len(invoices))
    approved_count = 0

    for invoice in invoices:
        status = _final_status(db, int(invoice.trn_id))
        label, tone = _OUTCOME.get(
            status, (status.replace("_", " ").capitalize(), "neutral")
        )
        data.outcomes[label] = data.outcomes.get(label, 0) + 1

        if status in ("paid", "approved"):
            approved_count += 1
        if status == "paid" and invoice.total is not None:
            data.total_paid += float(invoice.total)
        if status in ("fx_review_hold", "auditor_review", "rejected"):
            data.needs_attention += 1

        if len(data.recent) < RECENT_LIMIT:
            data.recent.append(
                RecentRow(
                    invoice_number=str(invoice.invoice_number),
                    merchant=str(invoice.merchant_name)
                    if invoice.merchant_name
                    else "Unknown supplier",
                    total=invoice.total,
                    status_label=label,
                    tone=tone,
                )
            )

    if data.processed:
        data.approval_rate = round(approved_count / data.processed * 100)
    return data
