"""The store, simulated.

This file is the measuring instrument, not the exercise: `make check` reads its
write log, so do not edit it. It behaves like a small hosted store with three
products and four rules:

  * `products/update` fires on every accepted write. Every one, including the
    writes the app itself made, and including a write that did not change the
    value you sent. That is what a real store does, and it is how a redundant
    write becomes a loop instead of a no-op.
  * the merchant installed one automation: a product that has stock on hand and
    a `DRAFT` status is flipped back to `ACTIVE`. It runs after every write. It
    is the merchant's, not yours; you do not get to change it.
  * forty writes to one product in one run and the store starts refusing with
    `Throttled`. That is the store's rate limit, and it is what turns an endless
    loop into something you can see in a log instead of a hung process.
  * the webhook is delivered synchronously, before `write()` returns. A real
    store does the same thing over the network, in the same window between your
    write and your next line of code; this lab collapses the network so the loop
    is reproducible instead of flaky. See the README.

The order inside `write()` is the order a real store runs it in, and it is the
order that matters: throttle, apply, automation, log, deliver, answer.
"""

from __future__ import annotations

THROTTLE_AFTER = 40

SEED = (
    {"gid": "gid://shopify/Product/101", "title": "Enamel mug", "status": "ACTIVE", "inventory_quantity": 12},
    {"gid": "gid://shopify/Product/102", "title": "Cotton tee", "status": "ACTIVE", "inventory_quantity": 40},
    {"gid": "gid://shopify/Product/103", "title": "Canvas cap", "status": "ACTIVE", "inventory_quantity": 7},
)


class Throttled(Exception):
    """The store refused the write: too many writes to one product in one run."""


class Store:
    def __init__(self, on_event=None) -> None:
        self.products = {row["gid"]: dict(row) for row in SEED}
        self.on_event = on_event if on_event is not None else (lambda event: None)
        self.writes: list[dict] = []
        self.counts = {gid: 0 for gid in self.products}

    def get(self, gid: str) -> dict:
        """The live read: a copy, so holding it does not pin the value."""
        return dict(self.products[gid])

    def write(self, gid: str, **changes) -> dict:
        # 1. the rate limit, counted per product, per run
        if self.counts[gid] >= THROTTLE_AFTER:
            raise Throttled(f"{gid}: {THROTTLE_AFTER} writes already, refusing more")

        before = dict(self.products[gid])
        # a payload that repeats the live value is recorded as redundant: the
        # store accepts it and fires a webhook anyway, which is exactly the trap
        redundant = all(before.get(field) == value for field, value in changes.items())

        # 2. apply what the caller asked for
        self.products[gid].update(changes)

        # 3. the merchant's automation, after every write
        product = self.products[gid]
        rewritten = []
        if product["inventory_quantity"] > 0 and product["status"] == "DRAFT":
            product["status"] = "ACTIVE"
            rewritten.append("status")

        # 4. the write log
        self.counts[gid] += 1
        self.writes.append(
            {
                "gid": gid,
                "sent": dict(changes),
                "before": before,
                "after": dict(product),
                "rewritten": rewritten,
                "redundant": redundant,
            }
        )

        # 5. the webhook, before this call returns
        self.on_event({"topic": "products/update", "gid": gid, "product": dict(product)})

        # 6. the answer
        return dict(product)
