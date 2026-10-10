"""Logika pemrosesan event pembayaran.

Kalau kamu perlu mengubah cara event diproses, ini file yang tepat.
"""

from decimal import Decimal

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from .models import Account, DeliveryAttempt, LedgerEntry


def apply_payment(
    session: Session,
    *,
    event_id: str,
    delivery_id: str,
    account_id: int,
    amount: float,
) -> tuple[int, dict]:
    """Catat satu pembayaran yang berhasil, lalu perbarui saldo akun.

    Gateway ini mengirim ulang event kalau jawaban dari kita tidak sampai ke
    mereka (timeout, koneksi putus, atau kita balas dengan error). Supaya
    pengiriman ulang tidak diproses dua kali, kita catat id tiap pengiriman dan
    memeriksanya lebih dulu di sini.
    """

    # Idempotensi.
    # Pengiriman dengan delivery_id ini sudah pernah kita proses, jadi tidak
    # ada yang perlu dikerjakan lagi. Ini yang bikin endpoint ini aman dipanggil
    # dua kali dengan request yang sama.
    already = session.execute(
        select(DeliveryAttempt.delivery_id).where(
            DeliveryAttempt.delivery_id == delivery_id
        )
    ).scalar_one_or_none()

    if already is not None:
        return 200, {
            "status": "ignored",
            "reason": "pengiriman ini sudah pernah diproses",
        }

    account = session.get(Account, account_id)
    if account is None:
        return 404, {"status": "error", "reason": f"akun {account_id} tidak ada"}

    nominal = Decimal(str(amount))

    entry = LedgerEntry(
        account_id=account_id,
        event_id=event_id,
        delivery_id=delivery_id,
        amount=nominal,
    )
    session.add(entry)

    account.balance = account.balance + nominal
    session.add(DeliveryAttempt(delivery_id=delivery_id, event_id=event_id))

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
