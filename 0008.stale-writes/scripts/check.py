#!/usr/bin/env python3
"""check.py — this lab's finish line.

Five checks, one theme: a message about the past cannot overwrite the present,
and a sale cannot take the shelf below zero.

    python3 scripts/check.py

Two checks read the venue count in `data/warehouse.json`. The other two run
their own small queue, so a change to the data file cannot make them pass.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

LAB = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(LAB))

from app.store import load_messages, load_warehouse, replay  # noqa: E402

SUMMARY = re.compile(r"summary messages=(\d+) applied=(\d+) rejected=(\d+)")

STALE_PROBE = [
    {"event_id": "p-1", "sku": "MUG-01", "type": "set", "quantity": 5, "event_time": "2026-11-09T10:00:00Z"},
    {"event_id": "p-2", "sku": "MUG-01", "type": "set", "quantity": 3, "event_time": "2026-11-09T09:00:00Z"},
]

SALE_PROBE = [
    {"event_id": "s-1", "sku": "CAP-03", "type": "set", "quantity": 1, "event_time": "2026-11-09T10:00:00Z"},
    {"event_id": "s-2", "sku": "CAP-03", "type": "sale", "quantity": 1, "event_time": "2026-11-09T10:01:00Z"},
    {"event_id": "s-3", "sku": "CAP-03", "type": "sale", "quantity": 1, "event_time": "2026-11-09T10:02:00Z"},
]


def main() -> int:
    messages = load_messages()
    warehouse = load_warehouse()
    skus = sorted(warehouse)

    stock = replay(messages, skus)
    system = stock.snapshot()

    results: list[tuple[str, str, bool, str]] = []

    # A — the number on file matches the number on the shelf.
    wrong = [f"{sku}: system {system[sku]}, venue {warehouse[sku]}" for sku in skus if system[sku] != warehouse[sku]]
    results.append((
        "A",
        "every product's quantity matches the venue count",
        not wrong,
        "all three match" if not wrong else "; ".join(wrong),
    ))

    # B — a message about the past does not overwrite the present.
    stale = replay(STALE_PROBE, skus)
    stale_ok = stale.snapshot()["MUG-01"] == 5 and stale.rejected >= 1
    results.append((
        "B",
        "an update older than the stored event time is rejected",
        stale_ok,
        f"after 5 then a late 3 from an hour earlier: MUG-01 = {stale.snapshot()['MUG-01']}, rejected {stale.rejected}",
    ))

    # C — nothing goes below zero, and a sale on an empty shelf changes nothing.
    probe = replay(SALE_PROBE, skus)
    probe_qty = probe.snapshot()["CAP-03"]
    negative = [f"{sku}: {system[sku]}" for sku in skus if system[sku] < 0]
    results.append((
        "C",
        "no quantity is negative, and a sale on an empty shelf is refused",
        not negative and probe_qty == 0,
        f"one item, then two sales: CAP-03 = {probe_qty}; negative rows in the replay: {', '.join(negative) or 'none'}",
    ))

    # D — the same event delivered twice changes nothing.
    twice = replay(messages + [messages[7]], skus).snapshot()
    results.append((
        "D",
        "a re-delivered event does not move the stock",
        twice == system,
        f"with e-302 delivered twice: {', '.join(f'{sku} {twice[sku]}' for sku in skus)}",
    ))

    # E — the consumer prints the same numbers it just acted on.
    proc = subprocess.run(
        [sys.executable, str(LAB / "app" / "consumer.py")],
        capture_output=True, text=True, cwd=LAB,
    )
    match = SUMMARY.search(proc.stdout)
    line = match.group(0) if match else (proc.stdout.strip().splitlines() or ["<no summary line>"])[-1]
    numbers_ok = (
        bool(match)
        and proc.returncode == 0
        and int(match.group(1)) == len(messages)
        and int(match.group(2)) + int(match.group(3)) == len(messages)
        and int(match.group(2)) == stock.applied
        and int(match.group(3)) == stock.rejected
    )
    results.append((
        "E",
        "the consumer prints one summary line with the counts it actually applied",
        numbers_ok,
        line,
    ))

    for code, title, ok, detail in results:
        print(f"{'PASS' if ok else 'FAIL'}  {code}  {title}")
        print(f"          {detail}")

    passed = sum(1 for _, _, ok, _ in results if ok)
    print()
    print(f"{passed} of {len(results)} checks passed")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
