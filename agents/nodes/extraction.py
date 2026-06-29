import logging

from agents.state import InvoiceState
from agents.tools.parsers import parse_invoice
from agents.tools.db import InvoiceDB
from agents.prompts.extraction import EXTRACTION_PROMPT
from llm import llm
from schemas import InvoiceExtraction
from config import MAX_EXTRACTION_ATTEMPTS

logger = logging.getLogger(__name__)


def extract_invoice(state: InvoiceState) -> dict:
    raw_text = parse_invoice(state["invoice_path"])
    base_prompt = EXTRACTION_PROMPT.format(invoice_text=raw_text)
    structured = llm.with_structured_output(InvoiceExtraction, include_raw=True)

    response: InvoiceExtraction | None = None
    last_error: object = None
    for attempt in range(MAX_EXTRACTION_ATTEMPTS):
        prompt = (
            base_prompt
            if attempt == 0
            else (
                f"{base_prompt}\n\nYour previous output failed schema validation with this error:\n"
                f"{last_error}\n\nReturn corrected output that satisfies the schema."
            )
        )
        result = structured.invoke([("human", prompt)])
        if result["parsing_error"] is None and result["parsed"] is not None:
            response = result["parsed"]
            break
        last_error = result["parsing_error"]
        logger.warning(
            f"Extraction attempt {attempt + 1}/{MAX_EXTRACTION_ATTEMPTS} failed: {last_error}"
        )

    if response is None:
        raise ValueError(
            f"Extraction failed after {MAX_EXTRACTION_ATTEMPTS} attempts: {last_error}"
        )

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
