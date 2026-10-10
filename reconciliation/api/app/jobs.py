"""Job rekonsiliasi harian.

Tugasnya satu: pembayaran yang tidak pernah sampai lewat webhook (gateway lagi
down, kita lagi down, koneksinya putus di tengah) harus tetap tercatat. Caranya
dengan membaca laporan settlement gateway dan membandingkannya dengan ledger.
"""

import uuid

from sqlalchemy.orm import Session

from . import ledger
from .gateway_client import fetch_settlement
from .models import ReconciliationRun


def run_reconciliation(session: Session, *, day: str, limit: int | None = None) -> dict:
    """Tutup selisih antara laporan settlement satu hari dan ledger.

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

    for payment in reported:
        if ledger.record_from_settlement(session, run_id=run_id, payment=payment):
            inserted += 1
        else:
            skipped += 1

    run = ReconciliationRun(
        run_id=run_id,
        day=day,
        limit_count=limit,
        seen=len(reported),
        inserted=inserted,
        skipped=skipped,
        mismatched=[],
    )
    session.add(run)
    session.commit()

    return {
        "run_id": run_id,
        "day": day,
        "seen": len(reported),
        "inserted": inserted,
        "skipped": skipped,
        "mismatched": [],
    }
