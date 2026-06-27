"""SQLAlchemy models for DB schema."""

from sqlalchemy import Column, Float, Integer, MetaData, Text, Date
from sqlalchemy.orm import declarative_base

metadata = MetaData()
Base = declarative_base(metadata=metadata)


class MasterInventory(Base):
    __tablename__ = "master_inventory"

    item_id = Column(Integer, primary_key=True, autoincrement=True)
    item_name = Column(Text)
    unit_price = Column(Float)
    item_budget = Column(Float, nullable=False)
    stock_qty = Column(Integer, nullable=False)


class MasterMerchant(Base):
    __tablename__ = "master_merchants"

    merchant_id = Column(Integer, primary_key=True, autoincrement=True)
    merchant_name = Column(Text, nullable=False, unique=True)
    rating = Column(Integer, nullable=False)
    on_time_history = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)


class TransactionInvoices(Base):
    __tablename__ = "transaction_invoices"

    trn_id = Column(Integer, nullable=False, primary_key=True, autoincrement=True)
    invoice_number = Column(Text, nullable=False)
    merchant_name = Column(Text, nullable=True)
    invoice_date = Column(Date, nullable=True)
    due_date = Column(Date, nullable=True)
    subtotal = Column(Float, nullable=True)
    tax = Column(Float, nullable=True)
    total = Column(Float, nullable=True)
    currency = Column(Text, nullable=True)
    source_file = Column(Text, nullable=True)


class TransactionAuditLogs(Base):
    __tablename__ = "transaction_audit_logs"

    audit_log_id = Column(Integer, primary_key=True, autoincrement=True)
    trn_id = Column(Integer, nullable=False)
    status = Column(Text, nullable=False, server_default="extracted")
    review_note = Column(Text, nullable=False, server_default="Invoice extracted")
    reviewed_by = Column(Text, nullable=False, server_default="Maker")
    payment_txn_id = Column(Text, nullable=True)
    updated_at = Column(Date, nullable=False, server_default="CURRENT_TIMESTAMP")


class TransactionInvoiceItems(Base):
    __tablename__ = "transaction_invoice_items"

    invoice_transaction_id = Column(Integer, primary_key=True, autoincrement=True)
    trn_id = Column(Integer, nullable=False)
    item_name = Column(Text, nullable=False)
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Float, nullable=False)
    line_total = Column(Float, nullable=False)
