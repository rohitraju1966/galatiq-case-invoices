import argparse
import logging
from agents.nodes.extraction import extract_invoice
from agents.nodes.validation import validate_invoice

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
    result = validate_invoice(state)
    logger.info(f"Validation: {result}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--invoice_path", required=True)
    args = parser.parse_args()
    main(args.invoice_path)
