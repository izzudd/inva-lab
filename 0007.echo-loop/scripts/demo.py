#!/usr/bin/env python3
"""demo.py — what the store's write log looks like right now.

    python3 scripts/demo.py
"""

from __future__ import annotations

import sys
from pathlib import Path

LAB = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(LAB))

from app import feed, sync  # noqa: E402
from store.store import Store  # noqa: E402

MUG = "gid://shopify/Product/101"
TEE = "gid://shopify/Product/102"
CAP = "gid://shopify/Product/103"


def line(number: int, write: dict) -> str:
    label = sync.sku_of(write["gid"]) if write["gid"] in sync.CATALOG else write["gid"]
    notes = []
    for field in write["rewritten"]:
        notes.append(f"automation set {field} -> {write['after'][field]}")
    if write["redundant"]:
        notes.append("payload already matched")

    out = []
    for field, value in write["sent"].items():
        old = write["before"].get(field)
        out.append(
            f"  {number:>3}  {label:<6}  {field:<20} {old!s:>6} -> {value!s:<16}"
            f"  {'; '.join(notes)}".rstrip()
        )
    return "\n".join(out)


def main() -> int:
    feed.load()
    sync.reset()

    queue: dict = {}
    store = Store(on_event=lambda event: sync.handle_event(event, store, queue))

    print("\nThe supplier's file says MUG-01 is gone. One product event arrives,\n"
          "the app syncs it, and this is every write the store accepted:\n")

    feed.set_available("MUG-01", False)
    sync.handle_event(sync.event_for(MUG), store, queue)
    first = sync.drain(store, queue)
    throttled = set(first["throttled"])
    for number, write in enumerate(store.writes, start=1):
        print(line(number, write))

    # the two other products, without their logs: same loop, nothing changed
    before = len(store.writes)
    store.write(TEE, title="Cotton tee (2026)")  # the merchant's own write, not the app's
    throttled |= set(sync.drain(store, queue)["throttled"])
    renamed = len(store.writes) - before

    sync.handle_event(sync.event_for(CAP), store, queue)
    idle = sync.drain(store, queue)
    throttled |= set(idle["throttled"])

    print()
    print(f"  A merchant renames TEE-01, touching nothing else: the store took "
          f"{renamed} write{'s' if renamed != 1 else ''} for it.")
    print(f"  Nothing about CAP-01 changed at all: {idle['writes']} writes followed.")
    print()
    print(f"writes={len(store.writes)}  throttled={len(throttled)}  "
          f"final={store.get(MUG)['status']}")
    print("\n  `make check` re-runs this in four scenarios and scores what it cost.\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
