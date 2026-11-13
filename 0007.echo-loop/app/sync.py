"""The app's two-way sync loop. This is the exercise.

The app mirrors three products from the supplier's file. For each product it
owns two fields in the store — `status` and `inventory_quantity` — and it writes
them back whenever the store says something happened:

    supplier file  ->  desired state  ->  store.write()  ->  products/update
                            ^                                      |
                            +--------------------------------------+

The last arrow is the one that should not exist twice. `handle_event()` is the
webhook handler, `drain()` is the worker that turns queued events into writes,
and `reconcile_all()` is the scheduled sync the demo runs.

Three things here are wrong on purpose. `HINTS.md` has one hint per thing.
"""

from __future__ import annotations

from dataclasses import dataclass

from app import feed
from store.store import Throttled

# the app's own catalog: store id -> supplier sku
CATALOG = {
    "gid://shopify/Product/101": "MUG-01",
    "gid://shopify/Product/102": "TEE-01",
    "gid://shopify/Product/103": "CAP-01",
}

# stock the app has zeroed, so it can put it back when the supplier returns
_STOCK: dict[str, int] = {}


def reset() -> None:
    """Forget everything the app remembered. The harness calls this per scenario."""
    _STOCK.clear()


def sku_of(gid: str) -> str:
    return CATALOG[gid]


@dataclass
class Job:
    gid: str


def handle_event(event: dict, store, queue: dict) -> None:
    """A `products/update` webhook arrived: queue the work, do not do it here."""
    if event.get("topic") != "products/update":
        return
    gid = event["gid"]
    if gid not in CATALOG:
        return
    # the newest event is the one worth acting on; the supplier's answer is read
    # when the job runs, not when the event arrived
    queue[gid] = Job(gid=gid)


def desired(gid: str, live: dict) -> dict:
    """The fields the app wants this product to have.

    The store's automation flips a DRAFT product with stock on hand back to
    ACTIVE, so a draft has to mean no stock on hand: the app owns both fields or
    it owns neither.
    """
    if not feed.available(sku_of(gid)):
        if live["inventory_quantity"] > 0:
            _STOCK[gid] = live["inventory_quantity"]
        return {"status": "DRAFT", "inventory_quantity": 0}
    return {
        "status": "ACTIVE",
        "inventory_quantity": _STOCK.get(gid, live["inventory_quantity"]),
    }


def drain(store, queue: dict) -> dict:
    """Work through the queue until it is empty, including what the writes add."""
    writes = 0
    throttled: set[str] = set()

    while queue:
        gid = next(iter(queue))
        queue.pop(gid)
        if gid in throttled:
            continue

        live = store.get(gid)
        changes = {
            field: value
            for field, value in desired(gid, live).items()
            if live.get(field) != value
        }
        if not changes:
            # the store already says what we wanted to say: nothing to send, and
            # nothing to echo back at us
            continue

        try:
            store.write(gid, **changes)
            writes += 1
        except Throttled:
            # the store stopped us; record it and let `make check` report it
            throttled.add(gid)

    return {"writes": writes, "throttled": sorted(throttled)}


def reconcile_all(store) -> dict:
    """The scheduled sync: every product in the catalog, one pass."""
    queue: dict[str, Job] = {}
    for gid in CATALOG:
        handle_event({"topic": "products/update", "gid": gid}, store, queue)
    return drain(store, queue)


def event_for(gid: str) -> dict:
    """The shape the store sends, for callers that want to fake one."""
    return {"topic": "products/update", "gid": gid}
