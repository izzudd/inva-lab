#!/usr/bin/env python3
"""Target lab ini. Hijau = kamu sudah selesai.

Jalankan dari root repo:  python3 scripts/check.py
"""

import json
import random
import sys
import urllib.error
import urllib.request
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import date, timedelta

BASE = "http://localhost:58102"
GATEWAY = "http://localhost:58103"
ACCOUNTS = [1, 2, 3]
CONCURRENT_RUNS = 2


# ---------------------------------------------------------------- alat bantu


def get_json(url: str):
    with urllib.request.urlopen(url, timeout=60) as response:
        return json.loads(response.read().decode())


def post_json(url: str, payload: dict, headers: dict | None = None) -> tuple[int, dict, str]:
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json", **(headers or {})},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            raw = response.read().decode()
            return response.status, json.loads(raw), raw
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode()
        try:
            return exc.code, json.loads(raw), raw
        except json.JSONDecodeError:
            return exc.code, {"raw": raw[:300]}, raw
    except Exception as exc:  # noqa: BLE001
        return 0, {"error": str(exc)}, ""


def is_2xx(status: int) -> bool:
    return 200 <= status < 300


def settle(day: str) -> list[dict]:
    """Laporan settlement gateway untuk satu hari (semua halaman)."""
    payments: list[dict] = []
    page = 1
    while True:
        data = get_json(f"{GATEWAY}/settlements/{day}?page={page}")
        payments.extend(data["payments"])
        if page >= data["pages"]:
            return payments
        page += 1


def new_day() -> str:
    """Tanggal acak: laporan gateway dibangkitkan dari tanggalnya, jadi tiap
    pemeriksaan dapat pembayaran yang baru tanpa perlu reset database."""
    rng = random.Random()
    return (date(2015, 1, 1) + timedelta(days=rng.randint(0, 3650))).isoformat()


def deliver(payment: dict, amount: float | None = None) -> tuple[int, dict, str]:
    return post_json(
        f"{BASE}/webhooks/payments",
        {
            "account_id": payment["account_id"],
            "charge_id": payment["charge_id"],
            "amount": payment["amount"] if amount is None else amount,
            "reference": payment["reference"],
        },
        {
            "X-Event-Id": f"evt_{uuid.uuid4().hex[:10]}",
            "X-Delivery-Id": f"dlv_{uuid.uuid4().hex[:10]}",
        },
    )


def reconcile(day: str, limit: int | None = None) -> tuple[int, dict, str]:
    return post_json(f"{BASE}/jobs/reconcile", {"day": day, "limit": limit})


def balance() -> float:
    return round(sum(float(get_json(f"{BASE}/api/accounts/{a}")["balance"]) for a in ACCOUNTS), 2)


def rows_for(charge_id: str) -> list[dict]:
    rows = []
    for account in ACCOUNTS:
        rows.extend(
            row
            for row in get_json(f"{BASE}/api/accounts/{account}/entries")
            if row["charge_id"] == charge_id
        )
    return rows


def rows_for_day(day: str) -> dict[str, list[dict]]:
    return {payment["charge_id"]: rows_for(payment["charge_id"]) for payment in settle(day)}


def total(payments: list[dict]) -> float:
    return round(sum(float(p["amount"]) for p in payments), 2)


# ------------------------------------------------------------------- kasusnya


def case_satu_jalur() -> list[tuple[str, bool, str]]:
    """Jalur webhook saja: tiga pembayaran, tiga baris."""
    day = new_day()
    payments = settle(day)
    before = balance()

    results = [deliver(payment) for payment in payments[:3]]

    counted = rows_for_day(day)
    rapi = all(len(counted[payment["charge_id"]]) == 1 for payment in payments[:3])
    naik = round(balance() - before, 2)

    return [
        (
            "A1 webhook biasa dicatat sekali",
            rapi and naik == total(payments[:3]),
            f"{sum(len(v) for v in counted.values())} baris, saldo naik {naik:.0f}",
        ),
        (
            "A2 semua webhook dijawab 2xx",
            all(is_2xx(status) for status, _, _ in results),
            f"{[status for status, _, _ in results]}",
        ),
    ]


def check_recon_menutup(day: str, payments: list[dict]) -> list[tuple[str, bool, str]]:
    """Job rekonsiliasi menutup yang belum tercatat."""
    before = balance()
    status, summary, _ = reconcile(day)

    counted = rows_for_day(day)
    dobel = [charge for charge, rows in counted.items() if len(rows) != 1]
    naik = round(balance() - before, 2)

    return [
        (
            "B1 setelah rekonsiliasi, satu pembayaran tetap satu baris",
            not dobel,
            "rapi" if not dobel else f"dobel: {dobel}",
        ),
        (
            "B2 saldo naik sebesar yang belum tercatat",
            naik == total(payments[3:]),
            f"naik {naik:.0f} (harusnya {total(payments[3:]):.0f})",
        ),
        (
            "B3 yang sudah tercatat tidak dicatat ulang oleh job",
            summary.get("inserted") == 3,
            f"job bilang inserted={summary.get('inserted')}, harusnya 3",
        ),
        ("B4 job dijawab 2xx", is_2xx(status), f"HTTP {status}"),
    ]


def case_recon_ulang(day: str) -> list[tuple[str, bool, str]]:
    """Job dijalankan lagi untuk hari yang sama."""
    before = balance()
    status, summary, _ = reconcile(day)
    naik = round(balance() - before, 2)
    counted = rows_for_day(day)
    dobel = [charge for charge, rows in counted.items() if len(rows) != 1]

    return [
        (
            "C1 jalan kedua tidak menambah baris",
            not dobel,
            "rapi" if not dobel else f"dobel: {dobel}",
        ),
        ("C2 jalan kedua tidak mengubah saldo", naik == 0, f"saldo naik {naik:.0f}"),
        (
            "C3 job melaporkan tidak ada yang baru",
            summary.get("inserted") == 0,
            f"inserted={summary.get('inserted')}, skipped={summary.get('skipped')}",
        ),
        ("C4 job dijawab 2xx", is_2xx(status), f"HTTP {status}"),
    ]


def case_webhook_telat(day: str, payments: list[dict]) -> list[tuple[str, bool, str]]:
    """Webhook untuk pembayaran yang sudah ditutup job akhirnya sampai."""
    telat = payments[3:]
    before = balance()
    results = [deliver(payment) for payment in telat]

    counted = rows_for_day(day)
    dobel = [p["charge_id"] for p in telat if len(counted[p["charge_id"]]) != 1]
    jumlah_salah = [
        p["charge_id"]
        for p in telat
        if any(abs(row["amount"] - float(p["amount"])) > 0.001 for row in counted[p["charge_id"]])
    ]
    naik = round(balance() - before, 2)

    return [
        ("D1 webhook telat tidak menambah baris", not dobel, "rapi" if not dobel else f"dobel: {dobel}"),
        ("D2 nominal yang sudah tercatat tidak berubah", not jumlah_salah, f"berubah: {jumlah_salah}"),
        ("D3 saldo tidak berubah", naik == 0, f"saldo naik {naik:.0f}"),
        (
            "D4 dijawab 2xx",
            all(is_2xx(status) for status, _, _ in results),
            f"{[status for status, _, _ in results]}",
        ),
    ]


def case_run_kepotong() -> list[tuple[str, bool, str]]:
    """Run yang cuma sempat memproses sebagian, lalu dijalankan lagi."""
    day = new_day()
    payments = settle(day)
    before = balance()

    status_pertama, summary_pertama, _ = reconcile(day, limit=2)
    status_kedua, _, _ = reconcile(day)

    counted = rows_for_day(day)
    dobel = [charge for charge, rows in counted.items() if len(rows) != 1]
    naik = round(balance() - before, 2)

    return [
        (
            "E1 run sepenggal (limit=2) cuma menulis dua pembayaran",
            summary_pertama.get("inserted") == 2 and status_pertama == 200,
            f"inserted={summary_pertama.get('inserted')}, HTTP {status_pertama}",
        ),
        (
            "E2 run penuh sesudahnya melengkapi tanpa mendobel",
            not dobel and naik == total(payments),
            f"{'rapi' if not dobel else f'dobel: {dobel}'}, saldo naik {naik:.0f} dari {total(payments):.0f}",
        ),
        ("E3 keduanya dijawab 2xx", is_2xx(status_pertama) and is_2xx(status_kedua), f"{status_pertama}/{status_kedua}"),
    ]


def case_nominal_beda() -> list[tuple[str, bool, str]]:
    """Laporan settlement beda nominal dengan yang sudah tercatat."""
    day = new_day()
    payments = settle(day)
    terakhir = payments[-1]
    beda = float(terakhir["amount"]) - 1000

    deliver(terakhir, amount=beda)
    before = balance()
    status, summary, _ = reconcile(day)

    counted = rows_for_day(day)
    rows = counted[terakhir["charge_id"]]
    naik = round(balance() - before, 2)
    dilaporkan = terakhir["charge_id"] in (summary.get("mismatched") or []) or terakhir["reference"] in (
        summary.get("mismatched") or []
    )

    return [
        ("F1 nominal yang sudah tercatat tidak ditimpa", len(rows) == 1 and abs(rows[0]["amount"] - beda) <= 0.001, f"{len(rows)} baris, nominal {rows[0]['amount'] if rows else '-'}"),
        (
            "F2 saldo tetap pakai nominal yang tercatat",
            naik == total(payments[:-1]),
            f"naik {naik:.0f} (harusnya {total(payments[:-1]):.0f})",
        ),
        (
            "F3 perbedaannya dilaporkan, bukan disembunyikan",
            dilaporkan,
            f"mismatched={summary.get('mismatched')}",
        ),
        ("F4 job dijawab 2xx", is_2xx(status), f"HTTP {status}"),
    ]


def case_run_tumpang_tindih() -> list[tuple[str, bool, str]]:
    """Dua run untuk hari yang sama, jalan bersamaan."""
    day = new_day()
    payments = settle(day)
    before = balance()

    with ThreadPoolExecutor(max_workers=CONCURRENT_RUNS) as pool:
        outcomes = list(pool.map(lambda _: reconcile(day), range(CONCURRENT_RUNS)))

    counted = rows_for_day(day)
    dobel = [charge for charge, rows in counted.items() if len(rows) != 1]
    naik = round(balance() - before, 2)

    return [
        (
            "G1 dua run bersamaan tetap satu baris per pembayaran",
            not dobel,
            "rapi" if not dobel else f"dobel: {dobel}",
        ),
        (
            "G2 saldo naik tepat sekali",
            naik == total(payments),
            f"naik {naik:.0f} dari {total(payments):.0f}",
        ),
        (
            "G3 keduanya dijawab 2xx",
            all(is_2xx(status) for status, _, _ in outcomes),
            f"{[status for status, _, _ in outcomes]}",
        ),
    ]


def main() -> int:
    try:
        get_json(f"{BASE}/health")
        get_json(f"{GATEWAY}/health")
    except Exception as exc:  # noqa: BLE001
        print(f"API/gateway belum jalan ({exc}). Jalankan `make up` dulu.")
        return 2

    print("\ncheck A - satu jalur: webhook")
    results_a = case_satu_jalur()

    day = new_day()
    payments = settle(day)
    deliver(payments[0])
    deliver(payments[1])
    deliver(payments[2])

    print("check B - job rekonsiliasi menutup yang belum tercatat")
    results_b = check_recon_menutup(day, payments)

    print("check C - job dijalankan lagi untuk hari yang sama")
    results_c = case_recon_ulang(day)

    print("check D - webhook yang telat nyusul")
    results_d = case_webhook_telat(day, payments)

    print("check E - run yang kepotong di tengah")
    results_e = case_run_kepotong()

    print("check F - nominal di laporan beda dengan yang tercatat")
    results_f = case_nominal_beda()

    print("check G - dua run bersamaan")
    results_g = case_run_tumpang_tindih()

    satu_baris = results_a + results_b + results_d + results_e + results_g
    boleh_diulang = results_c
    nominal = results_f

    print()
    for label, cases in (
        ("1. satu pembayaran, satu baris - dari jalur mana pun", satu_baris),
        ("2. job boleh dijalankan lagi, dan laporannya jujur", boleh_diulang),
        ("3. nominal yang sudah tercatat tidak berubah diam-diam", nominal),
    ):
        passed = all(ok for _, ok, _ in cases)
        print(f"  [{'LULUS' if passed else 'GAGAL'}] {label}")
        for name, ok, detail in cases:
            print(f"       [{'v' if ok else 'x'}] {name} - {detail}")
    print()

    all_cases = satu_baris + boleh_diulang + nominal
    failed = [name for name, ok, _ in all_cases if not ok]

    if not failed:
        print("Target tercapai. Dua hal terakhir untuk kamu periksa sendiri:")
        print("  1. `make demo` - cerita lengkapnya, sudah bersih sekarang.")
        print("  2. tanya ke dirimu: kunci apa yang kamu pakai, dan siapa yang punya kunci itu.")
        return 0

    print(f"Belum selesai: {len(failed)} dari {len(all_cases)} pemeriksaan merah.")
    print("Perhatikan pemeriksaan mana yang merah - gagalnya beda-beda, dan obatnya juga beda.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
