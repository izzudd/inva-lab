#!/usr/bin/env python3
"""Putar ulang satu event, persis seperti gateway melakukannya.

Gateway mengirim ulang event yang sama kalau jawabannya tidak sampai (timeout,
koneksi putus, atau kita membalas dengan error). Yang berubah cuma
X-Delivery-Id-nya - itu id pengiriman, bukan id eventnya.

Jalankan dari root repo:  python3 scripts/replay.py [jumlah pengiriman]
"""

import json
import sys
import urllib.error
import urllib.request
import uuid

BASE = "http://localhost:58100"
ACCOUNT_ID = 3
AMOUNT = 25000
SENDS = 4


def deliver(event_id: str, delivery_id: str, amount: int) -> tuple[int, str]:
    request = urllib.request.Request(
        f"{BASE}/webhooks/payments",
        data=json.dumps({"account_id": ACCOUNT_ID, "amount": amount}).encode(),
        headers={
            "Content-Type": "application/json",
            "X-Event-Id": event_id,
            "X-Delivery-Id": delivery_id,
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return response.status, response.read().decode()
    except urllib.error.HTTPError as exc:  # 4xx/5xx: tetap kita catat
        return exc.code, exc.read().decode()[:200]
    except Exception as exc:  # noqa: BLE001
        return 0, str(exc)


def get(path: str):
    with urllib.request.urlopen(f"{BASE}{path}", timeout=30) as response:
        return json.loads(response.read().decode())


def main() -> int:
    sends = int(sys.argv[1]) if len(sys.argv) > 1 else SENDS
    event_id = f"evt_{uuid.uuid4().hex[:8]}"

    try:
        account = get(f"/api/accounts/{ACCOUNT_ID}")
    except Exception as exc:  # noqa: BLE001
        print(f"API belum jalan di {BASE} ({exc}). Jalankan `make up` dulu.")
        return 2

    print(f"event  : {event_id}")
    print(f"jumlah : {sends} pengiriman, nominal {AMOUNT} tiap pengiriman")
    print(f"saldo sebelum: {account['balance']:.0f}\n")

    for i in range(1, sends + 1):
        status, body = deliver(event_id, f"dlv_{uuid.uuid4().hex[:8]}", AMOUNT)
        print(f"  pengiriman {i} -> HTTP {status}: {body}")

    account = get(f"/api/accounts/{ACCOUNT_ID}")
    entries = [e for e in get(f"/api/accounts/{ACCOUNT_ID}/entries") if e["event_id"] == event_id]

    print()
    print(f"baris ledger untuk event ini : {len(entries)}  (harusnya 1)")
    print(f"saldo sesudah               : {account['balance']:.0f}  (harusnya +{AMOUNT})")
    print()
    print("Kalau kamu membalik urutan dua angka itu - jumlah baris dan saldo -")
    print("kamu akan melihat polanya. Sekarang balik ke README.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
