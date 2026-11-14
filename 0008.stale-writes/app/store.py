"""store.py — the stock table, and the one function that applies a message.

This is the file you are meant to change. It runs on a dict, so a whole replay
takes milliseconds and prints the same numbers on every machine.

Two rules the store has to keep, and neither is enforced yet:

1. A message describes the quantity at `event_time`. A message that carries an
   older `event_time` than the row already holds is news about the past.
2. A sale cannot take the shelf below zero. The cap that just went out of stock
   is the one customers keep buying.

Nothing in this file talks to another system. The queue is `data/messages.json`
and the venue count is `data/warehouse.json`.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

LAB = Path(__file__).resolve().parent.parent
MESSAGES = LAB / "data" / "messages.json"
WAREHOUSE = LAB / "data" / "warehouse.json"


def load_messages(path: Path = MESSAGES) -> list[dict]:
    return json.loads(path.read_text(encoding="utf-8"))["messages"]


def load_warehouse(path: Path = WAREHOUSE) -> dict[str, int]:
    return dict(json.loads(path.read_text(encoding="utf-8"))["counted"])


def clock(stamp: str) -> datetime:
    return datetime.strptime(stamp, "%Y-%m-%dT%H:%M:%SZ")


class Stock:
    """The stock table. `rows[sku]` is `{"quantity": int, "event_time": str}`."""

    def __init__(self, skus: list[str]) -> None:
        self.rows = {sku: {"quantity": 0, "event_time": "1970-01-01T00:00:00Z"} for sku in skus}
        self.applied = 0
        self.rejected = 0
        self.stale_applied = 0
        self.sold_from_empty = 0

    def apply(self, message: dict) -> bool:
        """Apply one message. Returns True when it changed the row."""
        row = self.rows[message["sku"]]

        if message["type"] == "set":
            row["quantity"] = message["quantity"]
        else:
            if row["quantity"] <= 0:
                self.sold_from_empty += 1
            row["quantity"] -= message["quantity"]

        row["event_time"] = message["event_time"]
        self.applied += 1
        return True

    def snapshot(self) -> dict[str, int]:
        return {sku: row["quantity"] for sku, row in self.rows.items()}

    def summary(self) -> str:
        return f"summary messages={self.applied + self.rejected} applied={self.applied} rejected={self.rejected}"


def replay(messages: list[dict], skus: list[str]) -> Stock:
    stock = Stock(skus)
    for message in messages:
        stock.apply(message)
    return stock
