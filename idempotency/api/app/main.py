from fastapi import FastAPI, Header
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from . import handlers
from .db import SessionLocal

app = FastAPI(title="Inva Lab - Idempotency")


class PaymentEvent(BaseModel):
    account_id: int
    amount: float
    reference: str | None = None


@app.get("/health")
def health() -> dict:
    return {"ok": True}


@app.post("/webhooks/payments")
def receive_payment(
    payload: PaymentEvent,
    x_event_id: str = Header(..., alias="X-Event-Id"),
    x_delivery_id: str = Header(..., alias="X-Delivery-Id"),
):
    """Webhook dari gateway pembayaran. Dipanggil satu kali per pengiriman."""
    with SessionLocal() as session:
        status_code, body = handlers.apply_payment(
            session,
            event_id=x_event_id,
            delivery_id=x_delivery_id,
            account_id=payload.account_id,
            amount=payload.amount,
        )

    return JSONResponse(content=body, status_code=status_code)


@app.get("/api/accounts/{account_id}")
def get_account(account_id: int):
    with SessionLocal() as session:
        return handlers.account_snapshot(session, account_id)


@app.get("/api/accounts/{account_id}/entries")
def get_entries(account_id: int):
    with SessionLocal() as session:
        return handlers.list_entries(session, account_id)
