"""The supplier's stock file — the stable input the app derives state from.

One row per SKU: `sku,available`. The supplier overwrites the file whenever
something sells out or comes back; the app never writes to it.

`load()` re-reads the file and drops any change made through `set_available()`,
so every scenario in `scripts/` can start from the same world.
"""

from __future__ import annotations

import csv
from pathlib import Path

FEED = Path(__file__).resolve().parent.parent / "data" / "supplier.csv"

_STATE: dict[str, bool] = {}


def load(path: Path | str = FEED) -> dict[str, bool]:
    """Re-read the supplier file. Also undoes anything `set_available()` did."""
    rows: dict[str, bool] = {}
    with open(path, newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            rows[row["sku"].strip()] = row["available"].strip().lower() == "true"
    _STATE.clear()
    _STATE.update(rows)
    return dict(_STATE)


def available(sku: str) -> bool:
    """What the supplier says right now."""
    if not _STATE:
        load()
    return _STATE[sku]


def set_available(sku: str, value: bool) -> None:
    """The supplier changed one row.

    A real feed changes on its own, on the supplier's schedule. Here the harness
    plays the supplier so the change lands at a known moment instead of on a
    timer. `load()` puts every row back.
    """
    if not _STATE:
        load()
    _STATE[sku] = bool(value)
