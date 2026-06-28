import json
from pathlib import Path
import pandas as pd
import pdfplumber

def parse_invoice(invoice_path: str) -> str:
    file_path = Path(invoice_path)
    file_ext = file_path.suffix.lower()

    if file_ext not in {".txt", ".json", ".csv", ".xml", ".pdf"}:
        raise ValueError(f"Unsupported format: {file_ext}")

    try:
        if file_ext == ".txt" or file_ext == ".xml":
            return file_path.read_text()
        elif file_ext == ".json":
            return json.dumps(json.loads(file_path.read_text()), indent=2)
        elif file_ext == ".csv":
            return pd.read_csv(file_path).to_string(index=False)
        else:  # .pdf
            with pdfplumber.open(file_path) as pdf:
                return "\n".join(page.extract_text() or "" for page in pdf.pages)
    except (OSError, ValueError, pd.errors.ParserError) as e:
        raise ValueError(f"Failed to parse invoice {file_path}: {e}") from e
    
