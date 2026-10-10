"""Logika pemrosesan event pembayaran.

Kalau kamu perlu mengubah cara event diproses, ini file yang tepat.
"""

from decimal import Decimal

from fastapi import HTTPException
from sqlalchemy import select, update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from .models import Account, DeliveryAttempt, LedgerEntry, ProcessedEvent


def _claim_event(session: Session, event_id: str, fingerprint: str) -> bool:
    """Coba mengklaim satu event. True = kita yang dapat, False = sudah ada yang punya.

    Satu statement, bukan "SELECT dulu, baru INSERT". Kalau dua pengiriman datang
    bersamaan, tidak ada jendela waktu di antara periksa dan tulis yang bisa
    dilewati dua-duanya - database yang memutuskan, dan keputusannya cuma satu.
    """
    claimed = session.execute(
        pg_insert(ProcessedEvent)
        .values(event_id=event_id, request_fingerprint=fingerprint)
        .on_conflict_do_nothing(index_elements=[ProcessedEvent.event_id])
        .returning(ProcessedEvent.event_id)
    ).scalar_one_or_none()

    return claimed is not None


def apply_payment(
    session: Session,
    *,
    event_id: str,
    delivery_id: str,
    account_id: int,
    amount: float,
) -> tuple[int, dict]:
    """Catat satu pembayaran yang berhasil, lalu perbarui saldo akun.

    Gateway mengirim ulang event kalau jawaban dari kita tidak sampai. Pengiriman
    ulang bukan kesalahan siapa pun dan bukan kondisi luar biasa: itu caranya
    memastikan pesannya sampai. Jadi pengiriman ulang dijawab dengan jawaban yang
    sama seperti pengiriman pertama.
    """

    nominal = Decimal(str(amount)).quantize(Decimal("0.01"))

    # Isi request, diringkas jadi satu nilai. Dipakai untuk menjawab pertanyaan:
    # "event_id ini dipakai ulang dengan isi yang berbeda?"
    fingerprint = f"{account_id}:{nominal}"

    if session.get(Account, account_id) is None:
        return 404, {"status": "error", "reason": f"akun {account_id} tidak ada"}

    # 1. Klaim eventnya dulu. Kalau pengiriman ini kalah balapan, tidak ada
    #    pekerjaan yang dikerjakan sama sekali - dan tidak ada error yang perlu
    #    ditangani, karena konflik di sini hasil yang normal.
    if not _claim_event(session, event_id, fingerprint):
        session.rollback()  # klaimnya batal; transaksi ini tidak mengubah apa pun

        previous = session.get(ProcessedEvent, event_id)

        if previous is None:
            # Pengiriman lain memegang klaimnya dan belum commit. Jawab jujur:
            # belum selesai, coba lagi - jangan bilang sudah beres.
            return 503, {
                "status": "busy",
                "reason": "event ini sedang diproses pengiriman lain",
            }

        if previous.request_fingerprint != fingerprint:
            return 409, {
                "status": "conflict",
                "reason": "event_id ini sudah pernah dipakai dengan isi yang berbeda",
            }

        # 2. Sudah pernah diproses. Bukan error: kembalikan jawaban pengiriman
        #    pertama, persis seperti yang diterima gateway saat itu.
        return previous.response_status, previous.response_body

    # 3. Masih di transaksi yang sama dengan klaimnya: baris ledger dan saldo
    #    ikut commit bersama klaimnya. Kalau salah satu gagal, klaimnya ikut
    #    batal dan eventnya masih bisa diproses ulang.
    entry = LedgerEntry(
        account_id=account_id,
        event_id=event_id,
        delivery_id=delivery_id,
        amount=nominal,
    )
    session.add(entry)
    session.flush()  # supaya entry.id ada

    # Saldo dihitung oleh database. Baca-ubah-tulis di Python hilang kalau ada
    # event lain yang menyentuh akun yang sama pada saat yang bersamaan.
    balance = session.execute(
        update(Account)
        .where(Account.id == account_id)
        .values(balance=Account.balance + nominal)
        .returning(Account.balance)
    ).scalar_one()

    body = {
        "status": "applied",
        "entry_id": entry.id,
        "event_id": event_id,
        "account_id": account_id,
        "amount": float(nominal),
        "balance": float(balance),
    }

    session.execute(
        update(ProcessedEvent)
        .where(ProcessedEvent.event_id == event_id)
        .values(response_status=200, response_body=body)
    )

    # Catatan percobaan pengiriman tetap dipelihara, walau keputusannya sudah
    # pindah ke processed_events. Insert ini juga bisa bertabrakan, jadi ditulis
    # dengan cara yang sama: tabrakan = lewati, bukan gagal.
    session.execute(
        pg_insert(DeliveryAttempt)
        .values(delivery_id=delivery_id, event_id=event_id)
        .on_conflict_do_nothing(index_elements=[DeliveryAttempt.delivery_id])
    )

    session.commit()

    return 200, body


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
