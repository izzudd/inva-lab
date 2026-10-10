from fastapi import FastAPI, Header
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy import select

from . import jobs, ledger
from .db import SessionLocal
from .models import ReconciliationRun

app = FastAPI(title="Inva Lab - Reconciliation")


class PaymentEvent(BaseModel):
    account_id: int
    charge_id: str
    amount: float
    reference: str | None = None


class ReconcileJob(BaseModel):
    day: str
    limit: int | None = None


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
        status_code, body = ledger.record_from_webhook(
            session,
            event_id=x_event_id,
            delivery_id=x_delivery_id,
            charge_id=payload.charge_id,
            account_id=payload.account_id,
            amount=payload.amount,
        )

    return JSONResponse(content=body, status_code=status_code)


@app.post("/jobs/reconcile")
def reconcile(job: ReconcileJob):
    """Jalankan job rekonsiliasi untuk satu hari, sekali jalan."""
    with SessionLocal() as session:
        return jobs.run_reconciliation(session, day=job.day, limit=job.limit)


@app.get("/api/jobs")
def list_jobs():
    with SessionLocal() as session:
        rows = (
            session.execute(select(ReconciliationRun).order_by(ReconciliationRun.id))
            .scalars()
            .all()
        )

    return [
        {
            "run_id": row.run_id,
            "day": row.day.isoformat(),
            "limit": row.limit_count,
            "seen": row.seen,
            "inserted": row.inserted,
            "skipped": row.skipped,
            "mismatched": row.mismatched or [],
            "started_at": row.started_at.isoformat(),
        }
        for row in rows
    ]


@app.get("/api/accounts/{account_id}")
def get_account(account_id: int):
    with SessionLocal() as session:
        return ledger.account_snapshot(session, account_id)


@app.get("/api/accounts/{account_id}/entries")
def get_entries(account_id: int):
    with SessionLocal() as session:
        return ledger.list_entries(session, account_id)
