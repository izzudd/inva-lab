# Lab 7 — The webhook that talks to itself

Part of the [`inva-lab`](../README.md) repo. Every command below is run from the
`0007.echo-loop/` directory.

```bash
make demo     # the store's write log for one product, as it is now
make check    # this lab's target, seven checks
```

You mirror three products from a supplier's stock file into a store. The app owns
`status`: a product the supplier cannot supply is a `DRAFT`, everything else is
`ACTIVE`. The merchant, meanwhile, installed one automation in the store: a
product that has stock on hand and a `DRAFT` status is flipped back to `ACTIVE`.
Both rules are reasonable. Together they have no state they can agree on.

This is what the lab says, run as-is:

| command | what appears now |
|---|---|
| `make demo` | `writes=120  throttled=3  final=ACTIVE` — forty writes per product, and the product the supplier dropped is still on sale |
| `make check` | **0 of 7** checks green |
| the same demo on `solusi` | `writes=2  throttled=0  final=DRAFT`, and 7 of 7 green |

Nothing is broken in the way a stack trace breaks. `make demo` exits 0, every
write is accepted, the store never complains until it starts refusing, and no
line in the log is wrong on its own. The product is simply in the wrong state,
and the log repeats itself until the rate limit stops it.

## The loop

```
supplier file  ->  app decides status  ->  store.write(status="DRAFT")
                                                    |
                          the store's automation:   |  inventory > 0 and DRAFT
                          status = "ACTIVE"  <------+
                                                    |
                          products/update  ---------+--->  the app, again
```

The app writes `DRAFT`. The automation writes `ACTIVE`. The store fires a
webhook after *every* accepted write — including the app's own writes, and
including a write that did not change anything — so the app sees `ACTIVE`, still
believes the product should be `DRAFT`, and writes again. Forty rounds later the
store's rate limit is the only thing that ends it.

## Why this is not a webhook-plumbing bug

The obvious read is "our handler is too eager". It is: `app/sync.py` writes on
every `products/update` without comparing the payload to what the store already
has, so a rename costs forty writes. Fix that and the log gets quiet — and the
product the supplier dropped is *still* `ACTIVE`, because the automation flipped
it back and now nothing puts it back again. Check A is the one that notices.

The loop exists because two rules own the same field and disagree about it:

- the app: no supplier stock means `DRAFT`;
- the store: `inventory_quantity > 0` means it cannot be `DRAFT`.

Suppressing your own events hides the echo. It does not produce a fixed point.
The only way out is for the app to satisfy the store's invariant instead of
arguing with it: a product it drafts is a product with no stock on hand, so the
app has to write the number the automation reads, not just the status it wanted.
Then the automation has nothing to do, the webhook the app receives says what the
app already believes, and the loop stops because there is no next write to make.

## The instrument

`store/store.py` is the measuring instrument, not the exercise: `make check` reads
its write log, so do not edit it. It implements four behaviours:

- `products/update` fires on every accepted write, even when the payload did not
  change the value — that is what a real store does, and it is how a redundant
  write becomes a loop instead of a no-op;
- the merchant's automation runs after every write: `inventory_quantity > 0` and
  `status == "DRAFT"` becomes `ACTIVE`. It is not yours to change;
- forty writes to one product in one run and the store answers `Throttled`. That
  is the store's rate limit, and it is what turns an endless loop into a log you
  can read instead of a process that hangs;
- the webhook is delivered **synchronously**, inside `write()`, before it returns.
  A real store delivers it over the network, in the same window between your write
  and your next line of code. The lab collapses the network so the loop is
  reproducible instead of flaky.

`app/sync.py` is yours. `app/feed.py` reads `data/supplier.csv` and is the stable
input the app derives desired state from.

## Your mission

Make `make check` green. Seven checks in `scripts/check.py`, one theme:

> The echo is not the bug. The bug is that two rules own one field and disagree.
> Settle the ownership in the state, then stop sending writes that say nothing.

The three conditions behind the seven checks:

1. **One supplier change, one product, almost no writes.** A product the supplier
   marks unavailable ends `DRAFT`, and getting there costs at most two writes. No
   product in any scenario ever reaches the store's rate limit.
2. **Nothing else produces a write.** Renaming a product produces zero writes from
   the app, and no write is ever sent whose payload already equals the live value.
3. **The newest supplier answer wins.** A burst of five supplier updates, delivered
   before the worker runs, ends on the state the fifth implies, not the first. And
   when the supplier marks the product available again, it ends `ACTIVE` with the
   stock it had before — a draft you cannot undo is not a fix, it is a deletion.

## What this lab does not do

- **There is no concurrency.** One thread, one queue, no locks, no worker pool.
  The production advice that follows from this lab — one lane per product, so two
  workers cannot interleave writes to the same product — is not exercised here at
  all. Nothing in `make check` rewards it, and nothing punishes its absence. This
  lab is about who owns the field, not about how many workers are holding it.
- **It does not call a real store.** No network, no credentials, no HTTP. The
  store is a deterministic simulation, which is why the write counts are exact and
  reproducible. They are also not your store's numbers.
- **The rate limit is the lab's.** Forty writes is small on purpose. A real limit
  is per minute and per app, and a real loop usually hits it hours after the deploy.
- **Redundant writes are only counted, not priced.** A real store charges for API
  calls and counts them against a quota; here they only cost you a line in a log
  and, eventually, a refusal.

## Where the answers are

All answers live on the **`solusi`** branch:

```bash
git diff main solusi -- 0007.echo-loop/
```

Read [`HINTS.md`](HINTS.md) first. It has three levels, one per bug, and the first
one is enough for most people.
