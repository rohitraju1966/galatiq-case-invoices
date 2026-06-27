from langgraph.graph import StateGraph, END

from agents.state import InvoiceState
from agents.nodes.extraction import extract_invoice
from agents.nodes.validation import validate_invoice
from agents.nodes.vp import vp_review
from agents.nodes.management import management_review
from agents.nodes.payment import process_payment
from agents.tools.db import InvoiceDB
from config import APPROVAL_THRESHOLD, MAX_REVIEW_ROUNDS


def route_after_vp(state: InvoiceState) -> str:
    total = state.get("invoice_data", {}).get("total", 0) or 0
    review_count = state.get("review_count", 0)

    if total > APPROVAL_THRESHOLD and review_count < MAX_REVIEW_ROUNDS:
        db = InvoiceDB()
        db.log_audit(state["trn_id"], "management_review", f"Escalated: total ${total:,.2f} exceeds ${APPROVAL_THRESHOLD:,.0f} threshold", "graph")
        return "management"
    if state["status"] == "approved":
        return "payment"
    return END


builder = StateGraph(InvoiceState)

builder.add_node("extraction", extract_invoice)
builder.add_node("validation", validate_invoice)
builder.add_node("vp", vp_review)
builder.add_node("management", management_review)
builder.add_node("payment", process_payment)

builder.set_entry_point("extraction")
builder.add_edge("extraction", "validation")
builder.add_edge("validation", "vp")
builder.add_conditional_edges("vp", route_after_vp, {
    "management": "management",
    "payment": "payment",
    END: END,
})
builder.add_edge("management", "vp")
builder.add_edge("payment", END)

graph = builder.compile()
