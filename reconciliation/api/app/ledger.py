"""Mencatat pembayaran ke ledger.

Pembayaran yang sama bisa diberitahukan lewat dua jalur:

- **webhook** gateway — datang saat pembayarannya terjadi.
- **job rekonsiliasi** — jalan paginya, membaca laporan settlement dan menutup
  pembayaran yang webhook-nya tidak pernah sampai.

Kalau kamu perlu mengubah cara pembayaran dicatat, ini file yang tepat.
"""

from decimal import Decimal

from fastapi import HTTPException
from sqlalchemy import select, update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from .models import Account, LedgerEntry, ProcessedEvent


def _write_payment(
    session: Session,
    *,
    account_id: int,
    charge_id: str,
    event_id: str,
    delivery_id: str,
    source: str,
    nominal: Decimal,
) -> dict:
    entry = LedgerEntry(
        account_id=account_id,
        charge_id=charge_id,
        event_id=event_id,
        delivery_id=delivery_id,
        source=source,
        amount=nominal,
    )
    session.add(entry)
    session.flush()  # supaya entry.id ada

    # Saldo dihitung database: baca-ubah-tulis di Python hilang kalau ada
    # pembayaran lain yang menyentuh akun yang sama pada saat bersamaan.
    balance = session.execute(
        update(Account)
        .where(Account.id == account_id)
        .values(balance=Account.balance + nominal)
        .returning(Account.balance)
    ).scalar_one()

    return {
        "status": "applied",
        "entry_id": entry.id,
        "charge_id": charge_id,
        "event_id": event_id,
        "source": source,
        "account_id": account_id,
        "amount": float(nominal),
        "balance": float(balance),
    }


def _claim(session: Session, claim_key: str, fingerprint: str) -> bool:
    """Klaim satu kunci. True = kita yang dapat, False = sudah ada yang punya."""
    claimed = session.execute(
        pg_insert(ProcessedEvent)
        .values(event_id=claim_key, request_fingerprint=fingerprint)
        .on_conflict_do_nothing(index_elements=[ProcessedEvent.event_id])
        .returning(ProcessedEvent.event_id)
    ).scalar_one_or_none()

    return claimed is not None


def record_from_webhook(
    session: Session,
    *,
    event_id: str,
    delivery_id: str,
    charge_id: str,
    account_id: int,
    amount: float,
) -> tuple[int, dict]:
    """Jalur pertama: notifikasi langsung dari gateway."""
    nominal = Decimal(str(amount)).quantize(Decimal("0.01"))
    fingerprint = f"{charge_id}:{nominal}"

    if session.get(Account, account_id) is None:
        return 404, {"status": "error", "reason": f"akun {account_id} tidak ada"}

    if not _claim(session, event_id, fingerprint):
        session.rollback()
        previous = session.get(ProcessedEvent, event_id)

        if previous is None:
            return 503, {
                "status": "busy",
                "reason": "event ini sedang diproses pengiriman lain",
            }

        if previous.request_fingerprint != fingerprint:
            return 409, {
                "status": "conflict",
                "reason": "event_id ini sudah pernah dipakai dengan isi yang berbeda",
            }

        return previous.response_status, previous.response_body

    body = _write_payment(
        session,
        account_id=account_id,
        charge_id=charge_id,
        event_id=event_id,
        delivery_id=delivery_id,
        source="webhook",
        nominal=nominal,
    )

    session.execute(
        update(ProcessedEvent)
        .where(ProcessedEvent.event_id == event_id)
        .values(response_status=200, response_body=body)
    )
    session.commit()

    return 200, body


def record_from_settlement(session: Session, *, run_id: str, payment: dict) -> bool:
    """Jalur kedua: satu baris dari laporan settlement.

    Mengembalikan True kalau pembayarannya baru dicatat.

    Setiap baris ledger butuh id kejadian yang unik, dan jalur ini tidak punya
    id kejadian dari gateway - jadi id-nya dibuat di sini, dari id run ditambah
    kode charge. Klaimnya ditulis ke tabel yang sama dengan jalur webhook, biar
    tidak perlu tabel baru.
    """
    charge_id = payment["charge_id"]
    account_id = int(payment["account_id"])
    nominal = Decimal(str(payment["amount"])).quantize(Decimal("0.01"))

    claim_key = f"recon:{run_id}:{charge_id}"
    fingerprint = f"{charge_id}:{nominal}"

    if session.get(Account, account_id) is None:
        return False

    if not _claim(session, claim_key, fingerprint):
        session.rollback()
        return False

    body = _write_payment(
        session,
        account_id=account_id,
        charge_id=charge_id,
        event_id=claim_key,
        delivery_id=run_id,
        source="recon",
        nominal=nominal,
    )

    session.execute(
        update(ProcessedEvent)
        .where(ProcessedEvent.event_id == claim_key)
        .values(response_status=200, response_body=body)
    )
    session.commit()

    return True


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
            "charge_id": row.charge_id,
            "event_id": row.event_id,
            "delivery_id": row.delivery_id,
            "source": row.source,
            "amount": float(row.amount),
            "created_at": row.created_at.isoformat(),
        }
        for row in rows
    ]
