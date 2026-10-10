"""Logika pemrosesan event pembayaran.

Kalau kamu perlu mengubah cara event diproses, ini file yang tepat.
"""

from decimal import Decimal

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from .models import Account, LedgerEntry


def apply_payment(
    session: Session,
    *,
    event_id: str,
    delivery_id: str,
    account_id: int,
    amount: float,
) -> tuple[int, dict]:
    """Catat satu pembayaran yang berhasil, lalu perbarui saldo akun.

    Gateway mengirim eventnya lewat HTTP dan endpoint ini membalas 200 setelah
    transaksinya commit, jadi selama jalanan requestnya tidak bermasalah, satu
    event dari gateway sampai ke sini tepat satu kali.
    """
    nominal = Decimal(str(amount)).quantize(Decimal("0.01"))

    account = session.get(Account, account_id)
    if account is None:
        return 404, {"status": "error", "reason": f"akun {account_id} tidak ada"}

    entry = LedgerEntry(
        account_id=account_id,
        event_id=event_id,
        delivery_id=delivery_id,
        amount=nominal,
    )
    session.add(entry)

    account.balance = account.balance + nominal
    session.flush()  # supaya entry.id ada

    session.commit()

    return 200, {
        "status": "applied",
        "entry_id": entry.id,
        "event_id": event_id,
        "account_id": account_id,
        "amount": float(nominal),
        "balance": float(account.balance),
    }


def account_snapshot(session: Session, account_id: int) -> dict:
    account = session.get(Account, account_id)
    if account is None:
        raise HTTPException(status_code=404, detail=f"akun {account_id} tidak ada")

    return {
        "id": account.id,
        "name": account.name,
        "balance": float(account.balance),
    }


def list_entries(session: Session, account_id: int) -> list[dict]:
    rows = (
        session.execute(
            select(LedgerEntry)
            .where(LedgerEntry.account_id == account_id)
            .order_by(LedgerEntry.id)
        )
        .scalars()
        .all()
    )

    return [
        {
            "entry_id": row.id,
            "event_id": row.event_id,
            "delivery_id": row.delivery_id,
            "amount": float(row.amount),
            "created_at": row.created_at.isoformat(),
        }
        for row in rows
    ]
