"""Mencatat pembayaran ke ledger.

Pembayaran yang sama bisa diberitahukan lewat dua jalur:

- **webhook** gateway — datang saat pembayarannya terjadi.
- **job rekonsiliasi** — jalan paginya, membaca laporan settlement dan menutup
  pembayaran yang webhook-nya tidak pernah sampai.

Dua jalur, satu klaim: klaimnya tentang **pembayarannya** (`charge_id`), bukan
tentang pesannya. Yang berbeda cuma kebijakan waktu klaimnya sudah dipegang
pihak lain - dan itu memang boleh berbeda, karena penunggunya juga berbeda.

Kalau kamu perlu mengubah cara pembayaran dicatat, ini file yang tepat.
"""

from decimal import Decimal

from fastapi import HTTPException
from sqlalchemy import select, update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from .models import Account, LedgerEntry, PaymentClaim

# Hasil satu baris laporan settlement.
INSERTED = "inserted"
SKIPPED = "skipped"
MISMATCHED = "mismatched"
UNKNOWN_ACCOUNT = "unknown_account"
BUSY = "busy"


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


def _claim_payment(
    session: Session,
    *,
    charge_id: str,
    fingerprint: str,
    nominal: Decimal,
    source: str,
    message_id: str,
) -> bool:
    """Klaim satu pembayaran. True = kita yang dapat, False = sudah ada yang punya.

    Satu statement, dan kuncinya `charge_id` - sama untuk kedua jalur. Karena itu
    jalur mana pun yang datang belakangan akan menabrak baris yang sama, bukan
    membuat baris klaimnya sendiri.
    """
    claimed = session.execute(
        pg_insert(PaymentClaim)
        .values(
            charge_id=charge_id,
            first_seen_from=source,
            first_message_id=message_id,
            request_fingerprint=fingerprint,
            recorded_amount=nominal,
        )
        .on_conflict_do_nothing(index_elements=[PaymentClaim.charge_id])
        .returning(PaymentClaim.charge_id)
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
    """Jalur pertama: notifikasi langsung dari gateway.

    Kebijakannya: siapa pun yang mengirim ulang berhak mendapat jawaban yang sama
    seperti jawaban pertama, karena dia masih menunggu di ujung koneksi.
    """
    nominal = Decimal(str(amount)).quantize(Decimal("0.01"))
    fingerprint = f"{charge_id}:{nominal}"

    if session.get(Account, account_id) is None:
        return 404, {"status": "error", "reason": f"akun {account_id} tidak ada"}

    if not _claim_payment(
        session,
        charge_id=charge_id,
        fingerprint=fingerprint,
        nominal=nominal,
        source="webhook",
        message_id=event_id,
    ):
        session.rollback()
        previous = session.get(PaymentClaim, charge_id)

        if previous is None:
            return 503, {
                "status": "busy",
                "reason": "pembayaran ini sedang diproses pengiriman lain",
            }

        if previous.request_fingerprint != fingerprint:
            return 409, {
                "status": "conflict",
                "reason": "pembayaran ini sudah pernah dicatat dengan nominal yang berbeda",
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
        update(PaymentClaim)
        .where(PaymentClaim.charge_id == charge_id)
        .values(response_status=200, response_body=body)
    )
    session.commit()

    return 200, body


def record_from_settlement(session: Session, *, run_id: str, payment: dict) -> str:
    """Jalur kedua: satu baris dari laporan settlement.

    Kebijakannya beda dengan jalur webhook, dan itu disengaja: yang menunggu di
    ujung sini sebuah job, bukan koneksi HTTP. Job tidak boleh mati cuma karena
    satu baris laporan tidak cocok - baris begitu dilaporkan, lalu dilewati.
    """
    charge_id = payment["charge_id"]
    account_id = int(payment["account_id"])
    nominal = Decimal(str(payment["amount"])).quantize(Decimal("0.01"))
    fingerprint = f"{charge_id}:{nominal}"

    if session.get(Account, account_id) is None:
        return UNKNOWN_ACCOUNT

    if not _claim_payment(
        session,
        charge_id=charge_id,
        fingerprint=fingerprint,
        nominal=nominal,
        source="recon",
        message_id=run_id,
    ):
        session.rollback()
        previous = session.get(PaymentClaim, charge_id)

        if previous is None:
            # Run lain masih memegang klaimnya. Baris ini akan ikut di run
            # berikutnya - dan karena klaimnya per pembayaran, itu aman.
            return BUSY

        if previous.request_fingerprint != fingerprint:
            return MISMATCHED

        return SKIPPED

    body = _write_payment(
        session,
        account_id=account_id,
        charge_id=charge_id,
        event_id=f"recon:{run_id}:{charge_id}",
        delivery_id=run_id,
        source="recon",
        nominal=nominal,
    )

    session.execute(
        update(PaymentClaim)
        .where(PaymentClaim.charge_id == charge_id)
        .values(response_status=200, response_body=body)
    )
    session.commit()

    return INSERTED


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
