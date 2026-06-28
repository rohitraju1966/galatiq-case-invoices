from typing import TypedDict

class InvoiceState(TypedDict):
    invoice_path: str                    
    invoice_data: dict                   
    line_items: list[dict]               # Will be filled after extraction node
    validation_flags: list[str]          # Will be filled after validation node
    status: str                          # Will orchestrate the flow
    review_note: str                      
    reviewed_by: str                     
    trn_id: int                          # DB transaction ID (set after extraction inserts)
    payment_txn_id: str                  
    critique: str                        # Fed back to VP on revision pass, seperate from review note because VP will require both in the revision pass
    review_count: int                    # Tracks VP-auditor review rounds