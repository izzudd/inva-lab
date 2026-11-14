#!/usr/bin/env python3
"""consumer.py — read the queue, apply every message, print one line per message.

    python3 app/consumer.py

The last line is the summary the check parses. Do not change its shape:

    summary messages=11 applied=8 rejected=3
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.store import Stock, load_messages, load_warehouse  # noqa: E402


def main() -> int:
    messages = load_messages()
    skus = sorted(load_warehouse())
    stock = Stock(skus)

    for index, message in enumerate(messages, start=1):
        applied = stock.apply(message)
        row = stock.rows[message["sku"]]
        verdict = "applied" if applied else "rejected"
        stamp = message["event_time"][11:16]
        print(
            f"{index:>2}  {message['event_id']}  {message['sku']}  "
            f"{message['type']:<4}  {message['quantity']:>2}  @{stamp}  "
            f"{verdict:<8}  {message['sku']} = {row['quantity']}"
        )

    print()
    print(stock.summary())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
