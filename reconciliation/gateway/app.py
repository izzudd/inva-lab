"""Gateway pembayaran (tiruan).

Di lab ini gateway-nya cuma dibutuhkan untuk satu hal: laporan settlement harian.
Di dunia nyata laporan itu datang dari endpoint mereka, atau file CSV yang kamu
unduh tiap pagi. Isinya sama: daftar pembayaran yang menurut mereka sudah lunas.

Isi laporannya dibangkitkan dari tanggalnya, jadi tanggal yang sama selalu
menghasilkan pembayaran yang sama - dengan kode charge dan nominal yang sama.
Kamu bisa pakai tanggal apa pun.
"""

import hashlib
import random

from fastapi import FastAPI, Query

app = FastAPI(title="Inva Lab - Gateway")

PAGE_SIZE = 2
PAYMENTS_PER_DAY = 6
AMOUNTS = [10000, 15000, 25000, 50000, 75000]


def settlement_for(day: str) -> list[dict]:
    seed = int(hashlib.sha256(day.encode()).hexdigest()[:8], 16)
    rng = random.Random(seed)
    stamp = day.replace("-", "")

    payments = []
    for i in range(PAYMENTS_PER_DAY):
        payments.append(
            {
                "charge_id": f"ch_{stamp}{i + 1:02d}",
                "reference": f"ORDER-{stamp}-{i + 1:02d}",
                "account_id": (i % 3) + 1,
                "amount": float(rng.choice(AMOUNTS)),
                "paid_at": f"{day}T{10 + i // 2}:{(i % 2) * 30:02d}:00+07:00",
            }
        )
    return payments


@app.get("/health")
def health() -> dict:
    return {"ok": True}


@app.get("/settlements/{day}")
def settlements(day: str, page: int = Query(1, ge=1)) -> dict:
    rows = settlement_for(day)
    started = (page - 1) * PAGE_SIZE
    return {
        "day": day,
        "page": page,
        "page_size": PAGE_SIZE,
        "pages": (len(rows) + PAGE_SIZE - 1) // PAGE_SIZE,
        "total": len(rows),
        "payments": rows[started : started + PAGE_SIZE],
    }
