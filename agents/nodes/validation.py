import logging
from collections import defaultdict

from agents.state import InvoiceState
from agents.tools.db import InvoiceDB

logger = logging.getLogger(__name__)


def validate_invoice(state: InvoiceState) -> dict:
    db = InvoiceDB()
    data = state["invoice_data"]
    trn_id = state["trn_id"]
    flags: list[str] = []

    if db.is_duplicate(data["invoice_number"], trn_id):
        db.log_audit(trn_id, "rejected", "Duplicate invoice", "validation")
        return {"status": "rejected", "validation_flags": ["duplicate_invoice"]}

    # Currency convertion would require an API and as external API should not be used, flagging currencies other than USD and setting status as pending for approval along with VP reasoning
    is_foreign = (data.get("currency") or "USD") != "USD"
    if is_foreign:
        flags.append(
            f"foreign_currency: {data['currency']} (price/budget not verified against USD catalog)"
        )

    for item in state["line_items"]:
        master, was_normalized = db.get_item(item["item_name"])

        if not master:
            flags.append(f"unknown_item: {item['item_name']}")
            continue

        if was_normalized:
            flags.append(f"normalized_match: {item['item_name']} -> {master.item_name}")

        if not is_foreign and item["unit_price"] != master.unit_price:
            flags.append(
                f"price_mismatch: {item['item_name']} (invoice={item['unit_price']}, master={master.unit_price})"
            )

    # To make sure that we account for all the approved invoices and also to group all the similar items in the same invoice, we find total approved quantity and budge and group by for the invoice and find the total (sum of the two shoul be less than master inventory values)
    item_totals: dict[str, dict] = defaultdict(lambda: {"qty": 0, "spend": 0.0})
    for item in state["line_items"]:
        item_totals[item["item_name"]]["qty"] += item["quantity"]
        item_totals[item["item_name"]]["spend"] += item["quantity"] * item["unit_price"]

    for item_name, totals in item_totals.items():
        master, _ = db.get_item(item_name)
        if not master:
            continue

        approved = db.get_approved_totals(master.item_name, trn_id)

        if approved["qty"] + totals["qty"] > master.stock_qty:
            flags.append(
                f"stock_exceeded: {item_name} (approved={approved['qty']}, invoice={totals['qty']}, stock={master.stock_qty})"
            )

        if not is_foreign and approved["spend"] + totals["spend"] > master.item_budget:
            flags.append(
                f"budget_exceeded: {item_name} (approved={approved['spend']}, invoice={totals['spend']}, budget={master.item_budget})"
            )

    # Math checks
    for item in state["line_items"]:
        if item["line_total"] is None:
            continue
        expected = item["quantity"] * item["unit_price"]
        if abs(expected - item["line_total"]) > 0.01:
            flags.append(
                f"line_math_error: {item['item_name']} ({item['quantity']} x {item['unit_price']} != {item['line_total']})"
            )

    line_total_sum = sum(
        item["quantity"] * item["unit_price"] for item in state["line_items"]
    )
    if data["subtotal"] and abs(line_total_sum - data["subtotal"]) > 0.01:
        flags.append(
            f"subtotal_mismatch: (sum={line_total_sum}, subtotal={data['subtotal']})"
        )

    if data["subtotal"] and data["tax"] is not None and data["total"]:
        expected_total = data["subtotal"] + data["tax"]
        if abs(expected_total - data["total"]) > 0.01:
            flags.append(
                f"total_mismatch: (subtotal+tax={expected_total}, total={data['total']})"
            )

    # Merchant check
    if not data["merchant_name"]:
        flags.append("missing_merchant")
    elif not db.get_merchant(data["merchant_name"]):
        flags.append(f"unknown_merchant: {data['merchant_name']}")

    # Sanity checks
    for item in state["line_items"]:
        if (
            item["quantity"] < 0
            or item["unit_price"] < 0
            or (item["line_total"] or 0) < 0
        ):
            flags.append(f"negative_value: {item['item_name']}")
    if data["total"] and data["total"] < 0:
        flags.append("negative_total")

    note = " | ".join(flags) if flags else "All checks passed"
    db.log_audit(trn_id, "validated", note, "validation")
    logger.info(f"Validation complete for trn_id={trn_id}: {len(flags)} flags — {note}")

    return {
        "status": "validated",
        "validation_flags": flags,
    }
