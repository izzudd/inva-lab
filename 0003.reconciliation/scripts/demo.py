#!/usr/bin/env python3
"""Cerita lengkapnya, dalam empat babak.

    python3 scripts/demo.py 2026-10-09

Hari itu gateway-nya sempat down. Yang terjadi sesudahnya persis seperti ini.
"""

import json
import sys
import urllib.error
import urllib.request
import uuid

BASE = "http://localhost:58102"
GATEWAY = "http://localhost:58103"
ACCOUNTS = [1, 2, 3]
DAY = sys.argv[1] if len(sys.argv) > 1 else "2026-10-09"


def get_json(url: str):
    with urllib.request.urlopen(url, timeout=60) as response:
        return json.loads(response.read().decode())


def post_json(url: str, payload: dict, headers: dict | None = None):
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json", **(headers or {})},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            return response.status, response.read().decode()
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read().decode()[:200]


def settlement(day: str) -> list[dict]:
    payments: list[dict] = []
    page = 1
    while True:
        data = get_json(f"{GATEWAY}/settlements/{day}?page={page}")
        payments.extend(data["payments"])
        if page >= data["pages"]:
            return payments
        page += 1


def deliver(payment: dict) -> tuple[int, str]:
    return post_json(
        f"{BASE}/webhooks/payments",
        {
            "account_id": payment["account_id"],
            "charge_id": payment["charge_id"],
            "amount": payment["amount"],
            "reference": payment["reference"],
        },
        {"X-Event-Id": f"evt_{uuid.uuid4().hex[:10]}", "X-Delivery-Id": f"dlv_{uuid.uuid4().hex[:10]}"},
    )


def reconcile(day: str) -> tuple[int, str]:
    return post_json(f"{BASE}/jobs/reconcile", {"day": day})


def rows_for(charge_id: str) -> list[dict]:
    rows = []
    for account in ACCOUNTS:
        rows.extend(
            row
            for row in get_json(f"{BASE}/api/accounts/{account}/entries")
            if row["charge_id"] == charge_id
        )
    return rows


def balance() -> float:
    return round(sum(float(get_json(f"{BASE}/api/accounts/{a}")["balance"]) for a in ACCOUNTS), 2)


def show(payments: list[dict]) -> None:
    for payment in payments:
        rows = rows_for(payment["charge_id"])
        isi = ", ".join(f"{row['source']} {row['amount']:.0f}" for row in rows) or "-"
        print(f"   {payment['charge_id']}  {len(rows)} baris   [{isi}]")


def main() -> int:
    try:
        get_json(f"{BASE}/health")
    except Exception as exc:  # noqa: BLE001
        print(f"API belum jalan ({exc}). Jalankan `make up` dulu.")
        return 2

    payments = settlement(DAY)
    print(f"\nLaporan settlement gateway untuk {DAY}: {len(payments)} pembayaran,")
    print(f"total {sum(float(p['amount']) for p in payments):.0f}.\n")

    print("--- 19:00, tiga pembayaran pertama masuk lewat webhook ---")
    for payment in payments[:3]:
        status, _ = deliver(payment)
        print(f"   {payment['charge_id']}: HTTP {status}")
    show(payments)

    print("\n--- 23:40, gateway down. Tidak ada lagi webhook yang sampai ke kita ---")

    print("\n--- 06:00 paginya, job rekonsiliasi jalan untuk hari kemarin ---")
    status, body = reconcile(DAY)
    print(f"   HTTP {status}: {body}")
    show(payments)

    print("\n--- 11:20, gateway mengirim ulang webhook yang belum pernah dijawab ---")
    for payment in payments[3:]:
        status, _ = deliver(payment)
        print(f"   {payment['charge_id']}: HTTP {status}")
    show(payments)

    print(f"\nsaldo akun 1-3 sekarang: {balance():.0f}")
    print("yang seharusnya: nominal enam pembayaran di atas, masing-masing sekali.\n")
    print("Jalankan `make reset` kalau mau mengulang dari nol, atau `make check`")
    print("untuk melihat berapa banyak yang masih merah.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
