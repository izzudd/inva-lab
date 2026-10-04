#!/usr/bin/env python3
"""Ukur endpoint feed: latency dan jumlah query ke database.

Jalankan dari root repo:  python3 scripts/bench.py
"""

import json
import statistics
import sys
import time
import urllib.request

BASE = "http://localhost:58000"
ENDPOINT = f"{BASE}/api/posts?limit=20"
WARMUP = 2
RUNS = 10


def hit(url: str) -> tuple[float, int]:
    started = time.perf_counter()
    with urllib.request.urlopen(url, timeout=60) as response:
        response.read()
        headers = response.headers
    elapsed_ms = (time.perf_counter() - started) * 1000
    queries = int(headers.get("X-Db-Query-Count", "-1"))
    return elapsed_ms, queries


def main() -> int:
    try:
        hit(f"{BASE}/health")
    except Exception as exc:  # noqa: BLE001
        print(f"API belum jalan di {BASE} ({exc}).")
        print("Jalankan `make up` dulu.")
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
    p50 = statistics.median(latencies)
    p95 = latencies[min(len(latencies) - 1, int(0.95 * len(latencies)))]

    print(json.dumps(
        {
            "runs": RUNS,
            "query_per_request": {
                "min": min(query_counts),
                "max": max(query_counts),
            },
            "latency_ms": {
                "min": round(latencies[0], 1),
                "p50": round(p50, 1),
                "p95": round(p95, 1),
                "max": round(latencies[-1], 1),
            },
        },
        indent=2,
        ensure_ascii=False,
    ))
    return 0


if __name__ == "__main__":
    sys.exit(main())
