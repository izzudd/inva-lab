# Lab 8 — The stock that arrived out of order

Part of the [`inva-lab`](../README.md) repo. Every command below is run from the
`0008.stale-writes/` directory.

```bash
make demo   # what the system believes, next to what the venue counted
make run    # every message in arrival order, one line each
make check  # this lab's target
```

You run the stock service for a small online shop. Stock changes reach you as messages: a warehouse
worker scans a shelf and sends `set`, a customer buys and the shop sends `sale`. One queue, one
consumer, no concurrency, and every message applied the moment it arrives.

This is what `make demo` and `make check` say, run as-is:

| command | what appears |
|---|---|
| `make demo` | `CAP-03 -1` vs venue `0`, `MUG-01 4` vs venue `6`, `TEE-02 11` vs venue `9` |
| `make check` | **1 of 5** checks green |
| `make run` | 11 messages, `summary messages=11 applied=11 rejected=0` |

The cap that is out of stock still sells. The mug reads as four when six are on the shelf. Nothing
throws, the queue drains, the summary is tidy, and the only thing wrong is a number nobody checks
against the shelf.

## Why one queue produces three wrong shelves

Each message carries the quantity **at the moment it happened** in `event_time`, and the queue does
not promise you that order. Three of the eleven messages in `data/messages.json` arrive later than
the event they describe:

- **MUG-01** — `e-104` says six at 10:10, then `e-102` says four at 10:05 arrives after it. The older
  number lands last and wins, so the shelf reads four.
- **TEE-02** — the same shape with eleven and nine: the recount at 10:09 is overwritten by the 10:08
  message that arrived after it.
- **CAP-03** — three caps, two sold, then a recount of zero, then one more sale at 10:14. The sale
  takes the shelf to minus one, and the shop keeps selling a cap that is not there.

Every one of those is defensible in code review. The consumer applies what the message says, and the
message is not wrong: it is old. The queue has no opinion about time.

## Your mission

Make `make check` green. Five checks in `scripts/check.py`, one theme:

> A message about the past cannot overwrite the present, and a sale cannot take the shelf below
> zero.

Two of the checks read `data/warehouse.json`, the count a person made at 18:00. Three of them run
their own small queue, so editing the data file cannot make them pass:

- **A** every product's quantity matches the venue count;
- **B** an update older than the stored `event_time` is rejected, not applied;
- **C** no quantity is negative, and a sale on an empty shelf is refused;
- **D** a re-delivered event does not move the stock;
- **E** the consumer prints `summary messages=11 applied=N rejected=M` with the counts it actually
  applied, so the last line cannot lie about what happened above it.

The answer version passes all five and prints `summary messages=11 applied=8 rejected=3`: three
messages out of eleven describe a state that was already gone.

## What the starter gets right

The reporting. `make run` prints one line per message and a summary that matches the store's own
counters, which is why check E is the one check that is green before you touch anything. A consumer
that reports honestly and applies blindly is the ordinary case: the log tells you what it did, not
what it should have done.

## What this lab does not do

- **No broker.** The queue is a JSON array in arrival order. A real broker would let you test
  prefetch and re-delivery; here both are written into the file.
- **No concurrency.** One process, one lane. Serialising the messages would make this deterministic
  and hide the problem entirely, which is the trap the lab is built to avoid: the fix has to work
  when two workers exist, so it cannot be "apply them in the right order".
- **No storefront push.** The third path in the original story (retrying a push to another system)
  is out of scope here. Whether a fake storefront belongs in this lab is still an open decision.
- **`set` and `sale` are the whole vocabulary.** No reservations, no transfers between warehouses,
  no returns.

## Where the answers are

The working answer lives on the **`solusi-0008-stale-writes`** branch:

```bash
git diff main solusi-0008-stale-writes -- 0008.stale-writes/
```

Read [`HINTS.md`](HINTS.md) first. It has three levels, and the first one only asks you to put two
messages side by side.
