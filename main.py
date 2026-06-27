import argparse
import logging
from agents.nodes.extraction import extract_invoice
from agents.nodes.validation import validate_invoice
from agents.nodes.vp import vp_review

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
)

logger = logging.getLogger(__name__)

def main(invoice_path: str) -> None:
    logger.info(f"Processing the file: {invoice_path}")
    state = extract_invoice({"invoice_path": invoice_path})
    logger.info(f"Extraction: {state}")
    state = {**{"invoice_path": invoice_path}, **state}
    state = {**state, **validate_invoice(state)}
    logger.info(f"Validation: {state}")
    state = {**state, **vp_review(state)}
    logger.info(f"VP Review: {state}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--invoice_path", required=True)
    args = parser.parse_args()
    main(args.invoice_path)
