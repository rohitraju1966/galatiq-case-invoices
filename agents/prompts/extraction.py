EXTRACTION_PROMPT = """Role: Invoice data extraction agent.

Responsibilities: Extract all structured fields from the raw invoice text below.

Rules:
- Extract exactly what is written. Do not correct, guess, or infer missing fields.
- If a field is not present, set it to null.
- line_total is the per-line amount shown on the invoice. If a line shows only quantity and unit price with no amount, set line_total to null (do not compute it).
- Dates must be in YYYY-MM-DD format.
- Currency should be a 3-letter code (e.g. USD, EUR). Default to USD if not stated.

Example:
Input: "Invoice #1001 from Widgets Inc. Date: 2024-01-15. WidgetA x10 @ $250 = $2500. Subtotal: $2500. Tax: $250. Total: $2750."
Output:
{{
  "invoice_number": "1001",
  "merchant_name": "Widgets Inc.",
  "invoice_date": "2024-01-15",
  "due_date": null,
  "subtotal": 2500.00,
  "tax": 250.00,
  "total": 2750.00,
  "currency": "USD",
  "line_items": [
    {{"item_name": "WidgetA", "quantity": 10, "unit_price": 250.00, "line_total": 2500.00}}
  ]
}}

Invoice text:
{invoice_text}"""
