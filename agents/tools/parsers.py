import json
from pathlib import Path
import pandas as pd
import pdfplumber

def parse_invoice(invoice_path:str)->str:
    file_path=Path(invoice_path)
    file_ext = file_path.suffix.lower()

    if file_ext==".txt":
        return file_path.read_text()
    elif file_ext==".json":
        file_content=json.loads(file_path.read_text())
        return json.dumps(file_content, indent=2)       
    elif file_ext==".csv":
        df=pd.read_csv(file_path)
        return df.to_string(index=False)
    elif file_ext == ".xml":
        return file_path.read_text()
    elif file_ext == ".pdf":
        with pdfplumber.open(file_path) as pdf:
            return "\n".join(page.extract_text() or "" for page in pdf.pages)
    else:
        raise ValueError(f"Unsupported format: {file_ext}")
    
