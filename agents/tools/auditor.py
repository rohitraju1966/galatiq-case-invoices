from langchain_core.tools import tool
from agents.tools.db import InvoiceDB


def make_auditor_tools(trn_id: int) -> list:
    @tool
    def get_merchant_details(merchant_name: str) -> str:
        """Get merchant rating, on-time history, and notes from master records."""
        db = InvoiceDB()
        merchant = db.get_merchant(merchant_name)
        if not merchant:
            return "Merchant not found in master records."
        return f"Rating: {merchant.rating}/5, On-time: {merchant.on_time_history}, Notes: {merchant.notes}"

    @tool
    def get_item_details(item_name: str) -> str:
        """Get item price, stock, and budget from master inventory."""
        db = InvoiceDB()
        item, _ = db.get_item(item_name)
        if not item:
            return "Item not found in master inventory."
        return f"Price: ${item.unit_price}, Stock: {item.stock_qty}, Budget: ${item.item_budget}"

    @tool
    def get_invoice_history(merchant_name: str) -> str:
        """Get past invoices from this merchant."""
        db = InvoiceDB()
        invoices = db.get_invoice_history(merchant_name)
        if not invoices:
            return "No prior invoices from this merchant."
        return f"{len(invoices)} prior invoices from {merchant_name}"

    @tool
    def get_audit_trail() -> str:
        """Get the full decision history for this invoice — every status change, reviewer, and note."""
        db = InvoiceDB()
        logs = db.get_audit_trail(trn_id)
        if not logs:
            return "No audit trail found."
        lines = [f"[{log.status}] by {log.reviewed_by}: {log.review_note}" for log in logs]
        return "\n".join(lines)

    @tool
    def get_spending_summary(item_name: str) -> str:
        """Get cumulative approved quantity and spend for an item across all invoices."""
        db = InvoiceDB()
        totals = db.get_approved_totals(item_name, trn_id)
        return f"Approved so far: {totals['qty']} units, ${totals['spend']} spent"

    return [get_merchant_details, get_item_details, get_invoice_history, get_audit_trail, get_spending_summary]
