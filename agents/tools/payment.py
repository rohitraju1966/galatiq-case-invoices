import uuid


def mock_payment(merchant_name: str, amount: float) -> dict:
    return {
        "status": "success",
        "payment_txn_id": f"PAY-{uuid.uuid4().hex[:8].upper()}",
        "merchant": merchant_name,
        "amount": amount,
    }
