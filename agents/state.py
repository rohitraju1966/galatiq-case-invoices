from typing import TypedDict

class InvoiceState(TypedDict):
    invoice_path: str                    
    invoice_data: dict                   # extracted fields from LLM
    line_items: list[dict]               # extracted line items (will be filled after extraction node)
    validation_flags: list[str]          # flags from deterministic checks (will be filled after validation node)
    status: str                          # extracted -> validated -> approved/rejected/management_review -> paid  (will orchestrate the flow)
    review_note: str                     # VP/management reasoning (will be filled by either the VP or management)
    reviewed_by: str                     # which agent reviewed (VP/Management)
    trn_id: int                          # DB transaction ID (set after extraction inserts)
    payment_txn_id: str                  # set after payment 