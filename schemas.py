from pydantic import BaseModel, Field


class LineItem(BaseModel):
    item_name: str = Field(description="Product name as written on invoice")
    quantity: int = Field(description="Number of units ordered")
    unit_price: float = Field(description="Price per unit")
    line_total: float = Field(description="quantity * unit_price")


class InvoiceExtraction(BaseModel):
    invoice_number: str = Field(description="Invoice ID or number")
    merchant_name: str | None = Field(description="Vendor/supplier name")
    invoice_date: str | None = Field(description="Invoice date in YYYY-MM-DD")
    due_date: str | None = Field(description="Payment due date in YYYY-MM-DD")
    subtotal: float | None = Field(description="Sum of line totals before tax")
    tax: float | None = Field(description="Tax amount")
    total: float | None = Field(description="Final total including tax")
    currency: str = Field(default="USD", description="3-letter currency code")
    line_items: list[LineItem] = Field(description="Individual items on the invoice")
