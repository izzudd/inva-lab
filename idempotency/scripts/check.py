#!/usr/bin/env python3
"""Target lab ini. Hijau = kamu sudah selesai.

Jalankan dari root repo:  python3 scripts/check.py
"""

import json
import sys
import urllib.error
import urllib.request
import uuid
from concurrent.futures import ThreadPoolExecutor

BASE = "http://localhost:58100"
ACCOUNT_ID = 3  # akun yang saldonya masih nol, biar angkanya gampang dibaca

AMOUNT = 10000
REDELIVERIES = 4          # berapa kali satu event dikirim ulang, berurutan
CONCURRENT = 20           # berapa pengiriman bersamaan dalam satu putaran
CONCURRENT_ROUNDS = 3


def deliver(event_id: str, amount: float, delivery_id: str | None = None) -> tuple[int, dict, str]:
    """Kirim satu pengiriman. Mengembalikan (status HTTP, body, body mentah)."""
    request = urllib.request.Request(
        f"{BASE}/webhooks/payments",
        data=json.dumps({"account_id": ACCOUNT_ID, "amount": amount}).encode(),
        headers={
            "Content-Type": "application/json",
            "X-Event-Id": event_id,
            "X-Delivery-Id": delivery_id or f"dlv_{uuid.uuid4().hex[:10]}",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
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


def get_json(path: str):
    with urllib.request.urlopen(f"{BASE}{path}", timeout=30) as response:
        return json.loads(response.read().decode())


def balance() -> float:
    return round(float(get_json(f"/api/accounts/{ACCOUNT_ID}")["balance"]), 2)


def entries_for(event_id: str) -> list[dict]:
    rows = get_json(f"/api/accounts/{ACCOUNT_ID}/entries")
    return [row for row in rows if row["event_id"] == event_id]


def amount_for(event_id: str) -> float:
    return round(sum(row["amount"] for row in entries_for(event_id)), 2)


def new_event() -> str:
    return f"evt_{uuid.uuid4().hex[:10]}"


def is_2xx(status: int) -> bool:
    return 200 <= status < 300


def check_case_a() -> list[tuple[str, bool, str]]:
    """Satu event, satu pengiriman."""
    event = new_event()
    before = balance()
    status, body, _ = deliver(event, AMOUNT)

    rows = len(entries_for(event))
    delta = round(balance() - before, 2)

    return [
        ("A1 pengiriman pertama dijawab 2xx", is_2xx(status), f"HTTP {status}"),
        ("A2 satu baris ledger", rows == 1, f"{rows} baris"),
        ("A3 saldo naik tepat sekali", delta == AMOUNT, f"naik {delta:.0f}"),
    ]


def check_case_b() -> tuple[list[tuple[str, bool, str]], list[tuple[int, str]]]:
    """Satu event dikirim ulang berkali-kali, berurutan, tiap kiriman id-nya berbeda."""
    event = new_event()
    before = balance()

    results = [deliver(event, AMOUNT) for _ in range(REDELIVERIES)]

    rows = len(entries_for(event))
    delta = round(balance() - before, 2)

    return [
        ("B1 empat pengiriman, tetap satu baris ledger", rows == 1, f"{rows} baris"),
        ("B2 saldo naik tepat sekali", delta == AMOUNT, f"naik {delta:.0f}"),
    ], [(status, raw) for status, _, raw in results]


def check_case_c(bodies: list[tuple[int, str]]) -> list[tuple[str, bool, str]]:
    """Pengiriman ulang harus dijawab persis seperti jawaban pertama."""
    statuses = [status for status, _ in bodies]
    first = bodies[0][1]
    same = all(body == first for _, body in bodies)

    return [
        (
            "C1 semua pengiriman ulang dijawab 2xx",
            all(is_2xx(status) for status in statuses),
            f"status: {statuses}",
        ),
        (
            "C2 body pengiriman ulang identik dengan jawaban pertama",
            same,
            "sama" if same else f"beda: {bodies[0][1][:80]} vs {bodies[1][1][:80]}",
        ),
    ]


def check_case_d() -> list[tuple[str, bool, str]]:
    """Satu event dikirim 20 kali sekaligus. Retry yang tumpang tindih itu normal."""
    results: list[tuple[str, bool, str]] = []

    for round_no in range(1, CONCURRENT_ROUNDS + 1):
        event = new_event()
        before = balance()

        with ThreadPoolExecutor(max_workers=CONCURRENT) as pool:
            outcomes = list(pool.map(lambda _: deliver(event, AMOUNT), range(CONCURRENT)))

        applied = sum(1 for status, _, _ in outcomes if is_2xx(status) and status != 0)
        rows = len(entries_for(event))
        delta = round(balance() - before, 2)

        results.append(
            (
                f"D{round_no} {CONCURRENT} pengiriman bersamaan, tetap satu baris ledger",
                rows == 1,
                f"{rows} baris ({applied} dijawab 2xx, saldo naik {delta:.0f})",
            )
        )

    return results


def check_case_e() -> list[tuple[str, bool, str]]:
    """Tiga event berbeda, masing-masing dikirim dua kali. Semuanya harus masuk."""
    events = [new_event() for _ in range(3)]
    before = balance()

    for event in events:
        deliver(event, AMOUNT)
        deliver(event, AMOUNT)

    total_rows = sum(len(entries_for(event)) for event in events)
    delta = round(balance() - before, 2)

    return [
        ("E1 tiga event berbeda jadi tiga baris ledger", total_rows == 3, f"{total_rows} baris"),
        (
            "E2 saldo naik tiga kali lipat nominal",
            delta == 3 * AMOUNT,
            f"naik {delta:.0f}",
        ),
    ]


def check_case_f() -> list[tuple[str, bool, str]]:
    """event_id yang sama dipakai lagi, tapi isinya berbeda."""
    event = new_event()
    before = balance()

    deliver(event, 5000)
    status, _, _ = deliver(event, 999000)

    rows = len(entries_for(event))
    applied = amount_for(event)
    delta = round(balance() - before, 2)

    return [
        (
            "F1 nominal berbeda tidak ikut masuk",
            applied == 5000 and delta == 5000,
            f"tercatat {applied:.0f}, saldo naik {delta:.0f} (seharusnya 5000)",
        ),
        ("F2 tetap satu baris ledger", rows == 1, f"{rows} baris"),
        (
            "F3 dijawab 2xx (kembalikan jawaban lama) atau 4xx (tolak), bukan 5xx",
            is_2xx(status) or 400 <= status < 500,
            f"HTTP {status}",
        ),
    ]


def check_case_g() -> list[tuple[str, bool, str]]:
    """Banyak event berbeda datang bersamaan. Saldo harus tetap benar."""
    events = [new_event() for _ in range(CONCURRENT)]
    before = balance()

    with ThreadPoolExecutor(max_workers=CONCURRENT) as pool:
        list(pool.map(lambda event: deliver(event, AMOUNT), events))

    rows = sum(len(entries_for(event)) for event in events)
    delta = round(balance() - before, 2)

    return [
        (
            f"G1 {CONCURRENT} event berbeda jadi {CONCURRENT} baris ledger",
            rows == CONCURRENT,
            f"{rows} baris",
        ),
        (
            f"G2 saldo naik {CONCURRENT} kali nominal",
            delta == CONCURRENT * AMOUNT,
            f"naik {delta:.0f} dari {CONCURRENT * AMOUNT} yang seharusnya",
        ),
    ]


def main() -> int:
    try:
        get_json("/health")
    except Exception as exc:  # noqa: BLE001
        print(f"API belum jalan di {BASE} ({exc}). Jalankan `make up` dulu.")
        return 2

    print("\ncheck A - satu event, satu pengiriman")
    results_a = check_case_a()

    print("check B - satu event dikirim ulang berkali-kali")
    results_b, bodies = check_case_b()

    print("check C - pengiriman ulang dijawab sama")
    results_c = check_case_c(bodies)

    print(f"check D - {CONCURRENT} pengiriman bersamaan, {CONCURRENT_ROUNDS} putaran")
    results_d = check_case_d()

    print("check E - tidak ada event yang hilang")
    results_e = check_case_e()

    print("check F - event_id dipakai ulang dengan isi berbeda")
    results_f = check_case_f()

    print(f"check G - {CONCURRENT} event berbeda datang bersamaan")
    results_g = check_case_g()

    atomic = results_a + results_b + results_d + results_e
    replay = results_c
    conflict = results_f
    balance_under_load = results_g

    print()
    for label, cases in (
        ("1. tepat sekali - tidak dobel, tidak hilang", atomic),
        ("2. pengiriman ulang dijawab seperti jawaban pertama", replay),
        ("3. event_id yang dipakai ulang dengan isi berbeda", conflict),
        ("4. saldo tetap benar saat banyak event datang bersamaan", balance_under_load),
    ):
        passed = all(ok for _, ok, _ in cases)
        print(f"  [{'LULUS' if passed else 'GAGAL'}] {label}")
        for name, ok, detail in cases:
            print(f"       [{'v' if ok else 'x'}] {name} - {detail}")
    print()

    all_cases = atomic + replay + conflict + balance_under_load
    failed = [name for name, ok, _ in all_cases if not ok]

    if not failed:
        print("Target tercapai. Dua hal terakhir untuk kamu periksa sendiri:")
        print("  1. `make replay` - jalankan sampai beberapa kali, angkanya harus tetap.")
        print("  2. baca lagi SQL yang kamu pakai. Kalau kamu memutuskan di aplikasi")
        print("     (SELECT dulu, baru INSERT), coba jelaskan kenapa check D hijau.")
        return 0

    print(f"Belum selesai: {len(failed)} dari {len(all_cases)} pemeriksaan merah.")
    print("Perhatikan pemeriksaan mana yang merah - gagalnya beda-beda, dan obatnya juga beda.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
