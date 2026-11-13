#!/usr/bin/env python3
"""check.py — this lab's finish line.

Runs the app against a fresh simulated store, four times, and reads the store's
write log. Seven checks, one theme: the loop is a disagreement about who owns a
field, and the disagreement has to be settled in the state, not in the plumbing.

    python3 scripts/check.py
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

# Five supplier updates in a row, delivered before the app gets to work.
# The first says in stock; the fifth says gone. A queue that keeps the first
# event makes the oldest decision, and it is the wrong one.
BURST = [True, False, True, False, False]


class World:
    """One store, one app, one queue — fresh for every scenario."""

    def __init__(self) -> None:
        feed.load()
        sync.reset()
        self.queue: dict = {}
        self.store = Store(on_event=self.receive)

    def receive(self, event: dict) -> None:
        sync.handle_event(event, self.store, self.queue)

    def drain(self) -> dict:
        return sync.drain(self.store, self.queue)


def scenario_dark() -> dict:
    """The supplier marks one product unavailable; the app syncs it."""
    world = World()
    feed.set_available("MUG-01", False)
    world.receive(sync.event_for(MUG))
    result = world.drain()
    return {"store": world.store, "result": result, "final": world.store.get(MUG)}


def scenario_title() -> dict:
    """A merchant renames a product. Nothing else about it changes."""
    world = World()
    world.store.write(TEE, title="Cotton tee (2026)")  # the merchant's own write
    result = world.drain()
    return {
        "store": world.store,
        "result": result,
        "app_writes": len(world.store.writes) - 1,
    }


def scenario_burst() -> dict:
    """Five supplier updates arrive before the worker runs."""
    world = World()
    for value in BURST:
        feed.set_available("MUG-01", value)
        world.receive(sync.event_for(MUG))
    mark = len(world.store.writes)
    result = world.drain()

    # what the app first asked the store for after the burst; if it asked for
    # nothing, the live value is the decision that stood
    asked = [w["sent"]["status"] for w in world.store.writes[mark:] if "status" in w["sent"]]
    return {
        "store": world.store,
        "result": result,
        "decision": asked[0] if asked else world.store.get(MUG)["status"],
    }


def scenario_restock() -> dict:
    """One product goes unavailable, then comes back."""
    world = World()
    feed.set_available("MUG-01", False)
    world.receive(sync.event_for(MUG))
    first = world.drain()
    mid = world.store.get(MUG)

    feed.set_available("MUG-01", True)
    world.receive(sync.event_for(MUG))
    second = world.drain()
    return {
        "store": world.store,
        "result": {
            "writes": first["writes"] + second["writes"],
            "throttled": sorted(set(first["throttled"]) | set(second["throttled"])),
        },
        "mid": mid,
        "final": world.store.get(MUG),
    }


def main() -> int:
    dark = scenario_dark()
    title = scenario_title()
    burst = scenario_burst()
    restock = scenario_restock()
    worlds = [dark, title, burst, restock]

    results: list[tuple[str, str, bool, str]] = []

    # A — a product the supplier says is gone is drafted.
    status = dark["final"]["status"]
    results.append((
        "A",
        "a product the supplier marks unavailable ends up DRAFT",
        status == "DRAFT",
        f"MUG-01 status={status} after {dark['result']['writes']} "
        f"write{'s' if dark['result']['writes'] != 1 else ''}",
    ))

    # B — and getting there does not cost a write per webhook.
    writes = dark["result"]["writes"]
    results.append((
        "B",
        "that change costs at most 2 writes to the store",
        writes <= 2,
        f"{writes} write{'s' if writes != 1 else ''} to sync one product",
    ))

    # C — no product ever hits the store's rate limit.
    throttled = sorted({gid for world in worlds for gid in world["result"]["throttled"]})
    results.append((
        "C",
        "no product is ever throttled in any scenario",
        not throttled,
        f"{len(throttled)} product(s) throttled across {len(worlds)} scenarios"
        + (f": {', '.join(sync.sku_of(gid) for gid in throttled)}" if throttled else ""),
    ))

    # D — a title edit is not the app's business.
    results.append((
        "D",
        "changing only a product's title produces 0 writes",
        title["app_writes"] == 0,
        f"{title['app_writes']} app write(s) after 1 title edit",
    ))

    # E — the newest supplier update is the one that counts.
    results.append((
        "E",
        "a burst of five supplier changes ends on the fifth, not the first",
        burst["decision"] == "DRAFT",
        f"first decision after the burst: {burst['decision']}; "
        f"fifth update says DRAFT, first said ACTIVE",
    ))

    # F — and it can be undone: stock comes back, status comes back.
    restored = (
        restock["mid"]["status"] == "DRAFT"
        and restock["mid"]["inventory_quantity"] == 0
        and restock["final"]["status"] == "ACTIVE"
        and restock["final"]["inventory_quantity"] == 12
    )
    results.append((
        "F",
        "a product the supplier marks available again ends ACTIVE with its stock restored",
        restored,
        f"out: {restock['mid']['status']}/{restock['mid']['inventory_quantity']}, "
        f"back: {restock['final']['status']}/{restock['final']['inventory_quantity']}",
    ))

    # G — nothing is sent that the store already had.
    all_writes = [write for world in worlds for write in world["store"].writes]
    redundant = sum(1 for write in all_writes if write["redundant"])
    results.append((
        "G",
        "no write is ever issued whose payload already equals the live value",
        redundant == 0,
        f"{redundant} redundant of {len(all_writes)} writes",
    ))

    print()
    for tag, line, ok, detail in results:
        verdict = "GREEN" if ok else "RED  "
        print(f"  [{verdict}] {tag}. {line}  ({detail})")
    print()

    green = sum(1 for _, _, ok, _ in results if ok)
    total = len(results)
    if green == total:
        print(f"check: {green}/{total} green — done")
        return 0
    print(f"check: {green}/{total} green — not done yet")
    return 1


if __name__ == "__main__":
    sys.exit(main())
