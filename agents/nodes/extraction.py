import logging

from agents.state import InvoiceState
from agents.tools.parsers import parse_invoice
from agents.tools.db import InvoiceDB
from agents.prompts.extraction import EXTRACTION_PROMPT
from llm import llm
from schemas import InvoiceExtraction

logger = logging.getLogger(__name__)

def extract_invoice(state: InvoiceState) -> dict:
    raw_text = parse_invoice(state["invoice_path"])
    prompt = EXTRACTION_PROMPT.format(invoice_text=raw_text)
    response = llm.with_structured_output(InvoiceExtraction).invoke([("human", prompt)])

    db = InvoiceDB()
    trn_id = db.insert_invoice(response, state["invoice_path"])
    db.insert_line_items(trn_id, response)
    db.log_audit(trn_id, "extracted", "Invoice extracted", "extraction_agent")

    return {
        "invoice_data": response.model_dump(),
        "line_items": [item.model_dump() for item in response.line_items],
        "trn_id": trn_id,
        "status": "extracted",
    }
