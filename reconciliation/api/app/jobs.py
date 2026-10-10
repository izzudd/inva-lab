"""Job rekonsiliasi harian.

Tugasnya satu: pembayaran yang tidak pernah sampai lewat webhook (gateway lagi
down, kita lagi down, koneksinya putus di tengah) harus tetap tercatat.

Catatan penting soal bentuk job ini: **tidak ada kursor, tidak ada tabel progres,
tidak ada id run di kunci.** Menjalankan ulang satu hari penuh itu aman, karena
tiap pembayaran mengklaim dirinya sendiri. Job yang butuh mencatat "sudah sampai
mana" itu job yang datanya bisa ketinggalan atau dobel begitu run-nya berhenti di
tengah.
"""

import uuid

from sqlalchemy.orm import Session

from . import ledger
from .gateway_client import fetch_settlement
from .models import ReconciliationRun


def run_reconciliation(session: Session, *, day: str, limit: int | None = None) -> dict:
    """Cocokkan laporan settlement satu hari dengan ledger.

    `limit` cuma knob operasional: proses maksimal sekian pembayaran dalam satu
    run. Dipakai waktu mencoba job-nya di laptop, dan berguna kalau satu hari
    isinya puluhan ribu pembayaran.
    """
    run_id = f"run_{uuid.uuid4().hex[:8]}"
    reported = fetch_settlement(day)

    if limit is not None:
        reported = reported[:limit]

    inserted = 0
    skipped = 0
    mismatched: list[str] = []
    unknown_account: list[str] = []

    for payment in reported:
        outcome = ledger.record_from_settlement(session, run_id=run_id, payment=payment)

        if outcome == ledger.INSERTED:
            inserted += 1
        elif outcome == ledger.MISMATCHED:
            mismatched.append(payment["charge_id"])
        elif outcome == ledger.UNKNOWN_ACCOUNT:
            unknown_account.append(payment["charge_id"])
        else:
            skipped += 1

    run = ReconciliationRun(
        run_id=run_id,
        day=day,
        limit_count=limit,
        seen=len(reported),
        inserted=inserted,
        skipped=skipped,
        mismatched=mismatched,
    )
    session.add(run)
    session.commit()

    return {
        "run_id": run_id,
        "day": day,
        "seen": len(reported),
        "inserted": inserted,
        "skipped": skipped,
        "mismatched": mismatched,
        "unknown_account": unknown_account,
    }
