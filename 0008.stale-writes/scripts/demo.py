#!/usr/bin/env python3
"""demo.py — what the system believes, next to what the venue counted.

    python3 scripts/demo.py
"""

from __future__ import annotations

import sys
from pathlib import Path

LAB = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(LAB))

from app.store import load_messages, load_warehouse, replay  # noqa: E402


def main() -> int:
    messages = load_messages()
    warehouse = load_warehouse()
    stock = replay(messages, sorted(warehouse))
    system = stock.snapshot()

    print("sku      system   venue   verdict")
    for sku in sorted(warehouse):
        verdict = "same" if system[sku] == warehouse[sku] else "DIFFERENT"
        print(f"{sku:<8} {system[sku]:>6}  {warehouse[sku]:>6}   {verdict}")

    print()
    print(f"messages applied: {stock.applied}, rejected: {stock.rejected}")
    print(f"sales attempted on an empty shelf: {stock.sold_from_empty}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
