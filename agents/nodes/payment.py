import logging

from agents.state import InvoiceState
from agents.tools.db import InvoiceDB
from agents.tools.payment import mock_payment

logger = logging.getLogger(__name__)
db = InvoiceDB()


def process_payment(state: InvoiceState) -> dict:
    if state["status"] != "approved":
        return {}

    # Deterministic check (can be removed if we handle currency convertions on validation node, would require external API)
    if any(f.startswith("foreign_currency") for f in state.get("validation_flags", [])):
        logger.info("Payment blocked: unresolved foreign_currency flag")
        return {}

    merchant = state["invoice_data"].get("merchant_name", "Unknown")
    amount = state["invoice_data"].get("total", 0)

    result = mock_payment(merchant, amount)
    logger.info(f"Payment {amount} to {merchant}")

    db.log_audit(state["trn_id"], "paid", f"Payment to {merchant}: ${amount}", "payment", payment_txn_id=result["payment_txn_id"])

    return {
        "status": "paid",
        "payment_txn_id": result["payment_txn_id"],
    }
