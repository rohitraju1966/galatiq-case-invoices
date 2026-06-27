from langchain_core.tools import tool
from agents.tools.db import InvoiceDB

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