import logging
from datetime import date
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from config import DB_PATH
import re

from sqlalchemy import func

from db.models import TransactionInvoices, TransactionInvoiceItems, TransactionAuditLogs, MasterInventory, MasterMerchant
from schemas import InvoiceExtraction

logger = logging.getLogger(__name__)

class InvoiceDB:
    def __init__(self):
        engine = create_engine(f"sqlite:///{DB_PATH}")
        self.session=sessionmaker(bind=engine)()
    
    @staticmethod
    def _parse_date(val: str | None) -> date | None:
        return date.fromisoformat(val) if val else None

    def insert_invoice(self, data: InvoiceExtraction, source_file: str)->int:
        invoice = TransactionInvoices(
            invoice_number=data.invoice_number,
            merchant_name=data.merchant_name,
            invoice_date=self._parse_date(data.invoice_date),
            due_date=self._parse_date(data.due_date),
            subtotal=data.subtotal,
            tax=data.tax,
            total=data.total,
            currency=data.currency,
            source_file=source_file,
        )
        self.session.add(invoice)
        self.session.commit()
        logger.info(f"Inserted invoice {data.invoice_number}, trn_id={invoice.trn_id}")
        return invoice.trn_id
    
    def insert_line_items(self, trn_id: int, data: InvoiceExtraction)->None:
        for item in data.line_items:
            row = TransactionInvoiceItems(
                trn_id=trn_id,
                item_name=item.item_name,
                quantity=item.quantity,
                unit_price=item.unit_price,
                line_total=item.line_total,
            )
            self.session.add(row)
        
        self.session.commit()
        logger.info(f"Inserted {len(data.line_items)} line items for trn_id={trn_id}")
    
    def log_audit(self, trn_id: int, status: str, note: str, reviewed_by: str, payment_txn_id: str | None = None) -> None:
        log = TransactionAuditLogs(
            trn_id=trn_id,
            status=status,
            review_note=note,
            reviewed_by=reviewed_by,
            payment_txn_id=payment_txn_id,
            updated_at=date.today(),
        )
        self.session.add(log)
        self.session.commit()
        logger.info(f"Audit log: trn_id={trn_id}, status={status}, by={reviewed_by}")

    def is_duplicate(self, invoice_number: str, current_trn_id: int) -> bool:
        return self.session.query(TransactionAuditLogs).join(
            TransactionInvoices,
            TransactionAuditLogs.trn_id == TransactionInvoices.trn_id,
        ).filter(
            TransactionInvoices.invoice_number == invoice_number,
            TransactionInvoices.trn_id != current_trn_id,
            TransactionAuditLogs.status == "approved",
        ).first() is not None

    def get_item(self, item_name: str) -> tuple[MasterInventory | None, bool]:
        direct = self.session.query(MasterInventory).filter(
            MasterInventory.item_name == item_name,
        ).first()
        if direct:
            return direct, False

        normalized = re.sub(r"[^a-z0-9]", "", item_name.lower())
        for item in self.session.query(MasterInventory).all():
            if re.sub(r"[^a-z0-9]", "", item.item_name.lower()) == normalized:
                return item, True

        return None, False

    def get_approved_totals(self, item_name: str, current_trn_id: int) -> dict:
        
        # Query the total quantity and purchased sum for a product where the invoice status has moved to approved 
        result = self.session.query(
            func.coalesce(func.sum(TransactionInvoiceItems.quantity), 0),
            func.coalesce(func.sum(TransactionInvoiceItems.line_total), 0),
        ).join(
            TransactionInvoices,
            TransactionInvoiceItems.trn_id == TransactionInvoices.trn_id,
        ).join(
            TransactionAuditLogs,
            TransactionAuditLogs.trn_id == TransactionInvoices.trn_id,
        ).filter(
            TransactionInvoiceItems.item_name == item_name,
            TransactionAuditLogs.status == "approved",
            TransactionInvoices.trn_id != current_trn_id,
        ).first()

        return {"qty": result[0], "spend": result[1]}

    def get_merchant(self, merchant_name: str) -> MasterMerchant | None:
        return self.session.query(MasterMerchant).filter(
            MasterMerchant.merchant_name == merchant_name,
        ).first()
    
    def get_invoice_history(self, merchant_name: str) -> list:
        return self.session.query(TransactionInvoices).filter(
            TransactionInvoices.merchant_name == merchant_name,
        ).all()

    def get_audit_trail(self, trn_id: int) -> list[TransactionAuditLogs]:
        return self.session.query(TransactionAuditLogs).filter(
            TransactionAuditLogs.trn_id == trn_id,
        ).order_by(TransactionAuditLogs.audit_log_id).all()
