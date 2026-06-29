import argparse
import logging
from agents.graph import graph

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
)

logger = logging.getLogger(__name__)


def main(invoice_path: str) -> None:
    logger.info(f"Processing the file: {invoice_path}")
    result = graph.invoke({"invoice_path": invoice_path})
    logger.info(
        f"Final result: status={result['status']}, reviewed_by={result.get('reviewed_by')}"
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--invoice_path", required=True)
    args = parser.parse_args()
    main(args.invoice_path)
