#!/usr/bin/env python3
"""Target lab ini. Hijau = kamu sudah selesai.

Jalankan dari root repo:  python3 scripts/check.py
"""

import statistics
import sys
import time
import urllib.request

BASE = "http://localhost:58000"
ENDPOINT = f"{BASE}/api/posts?limit=20"
WARMUP = 2
RUNS = 10

MAX_QUERIES_PER_REQUEST = 3
MAX_P95_MS = 30.0


def hit(url: str) -> tuple[float, int]:
    started = time.perf_counter()
    with urllib.request.urlopen(url, timeout=60) as response:
        response.read()
        queries = int(response.headers.get("X-Db-Query-Count", "-1"))
    return (time.perf_counter() - started) * 1000, queries


def main() -> int:
    try:
        hit(f"{BASE}/health")
    except Exception as exc:  # noqa: BLE001
        print(f"API belum jalan di {BASE} ({exc}). Jalankan `make up` dulu.")
        return 2

    for _ in range(WARMUP):
        hit(ENDPOINT)

    latencies: list[float] = []
    query_counts: list[int] = []
    for _ in range(RUNS):
        elapsed_ms, queries = hit(ENDPOINT)
        latencies.append(elapsed_ms)
        query_counts.append(queries)

    latencies.sort()
    p95 = latencies[min(len(latencies) - 1, int(0.95 * len(latencies)))]
    worst_queries = max(query_counts)

    results = [
        (
            f"query per request <= {MAX_QUERIES_PER_REQUEST} (terburuk: {worst_queries})",
            worst_queries <= MAX_QUERIES_PER_REQUEST,
        ),
        (
            f"latency p95 <= {MAX_P95_MS:.0f}ms (p95: {p95:.1f}ms)",
            p95 <= MAX_P95_MS,
        ),
    ]

    print()
    for label, ok in results:
        print(f"  [{'LULUS' if ok else 'GAGAL'}] {label}")
    print()

    if all(ok for _, ok in results):
        print("Target tercapai. Cek satu hal terakhir: apakah hasilnya masih benar?")
        print("Bandingkan body response sebelum dan sesudah perubahan kamu.")
        return 0

    print("Belum selesai. Ada dua cara berbeda untuk gagal di sini -")
    print("perhatikan mana yang masih merah sebelum memilih langkah berikutnya.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
