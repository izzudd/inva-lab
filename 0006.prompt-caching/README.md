# Lab 6 — The cache that never hits

Part of the [`inva-lab`](../README.md) repo. Every command below is run from the
`0006.prompt-caching/` directory.

```bash
make demo     # what the bill looks like now, per ticket
make bench    # the same loop, turn by turn (ID=T-1043 for one ticket)
make what-changes  # two consecutive requests, block by block
make check    # this lab's target
```

You have a support agent that answers tickets. It carries a six-thousand-word
handbook in its prompt, five tool definitions, and the growing transcript of the
conversation. Prompt caching is on: the provider has cached the prefix, the model
gives the same answers, and the bills do not match the token counter.

This is what `make demo` and `make check` say, run as-is:

| command | what appears now |
|---|---|
| `make demo` | `hit=  0.0%  $0.4841` for all three tickets |
| `make check` | **0 of 7** checks green |
| the same loop, `cache_enabled=False` | `$0.4017` — **caching costs 21% more than not caching** |

Nothing is broken in the way a stack trace breaks. Every ticket is answered, the
loop exits 0, and the provider reports nothing unusual. The bill is just wrong,
and the only thing that says so is a number you have to go looking for.

## Why the bill is higher than the price list

A cache hit is not a property of the feature you enabled. It is a property of the
bytes you send: the provider hashes the prefix up to a breakpoint you marked, and
it can only reuse an entry that a *previous* request wrote at a boundary it will
look at again this time. One changed byte in the prefix, one breakpoint in the
wrong place, or one entry that expired is enough to pay the write price for the
whole prompt and collect nothing.

The provider in this lab implements one vendor's documented rules, published in
November 2026:

- a cache entry is written **only** at a block you marked as a breakpoint;
- a read looks backward from the breakpoint, at most **20 block positions**, and
  takes the first entry a previous request actually wrote;
- a prefix shorter than **512 tokens** cannot be cached at all;
- **5 minutes** by default, **1 hour** if you ask for it, refreshed for free on
  every read;
- a write costs **1.25x** the input price, a read costs **0.1x**.

`agent/provider.py` is that rulebook made runnable. It is the measuring
instrument, not the exercise: do not edit it. Everything else in `agent/` is
yours.

## Your mission

Make `make check` green. Seven checks in `scripts/check.py`, one theme:

> The cache follows the bytes. Order the prompt by how often each part changes,
> put the breakpoint at the end of the part that does not change, and measure the
> hit rate instead of believing the feature flag.

The three conditions behind the seven checks:

1. **The same request, twice, must reuse its prefix.** At least 75% of the tokens
   you send come back as cache reads, and the run costs at most 45% of the same
   run with caching off. Two different tickets must not poison each other's
   prefix.
2. **The model must still get what it needs.** Today's date has to reach the
   model — moving it out of the prompt is not a fix. The tools array has to be
   byte-identical from the first turn to the last, and every request has to be
   the previous request plus new blocks, never a rewrite of the old ones.
3. **The loop must survive a pause and say so.** The customer goes quiet for ten
   minutes after turn four; the turn that follows still has to read the handbook
   from cache. And `python3 agent/loop.py` must print one line with the numbers it
   measured:

   ```
   summary turns=24 hit_rate=0.909 cost_usd=0.143682
   ```

`make bench` is how you find the shape of the problem before you touch anything:
it prints, per turn, how many tokens were sent, how many were read from cache,
how many were written, and what that cost.

## Where the cost you are chasing is

The static prefix — handbook plus tool definitions — is 6,135 tokens; the transcript grows
by roughly 320 tokens a turn.
Over eight turns the static block is most of every request, which is why caching
it correctly is worth more than making it shorter — but only while the transcript
is thin. Past ten turns the transcript dominates and the handbook stops being the
lever. `make bench` shows both numbers on the same row, which is the point.

## What this lab does not do

- **It does not call a real provider.** No key, no network, no bill. The engine
  is a deterministic simulation of one vendor's published rules, so the numbers
  are reproducible and free; they are also *not* what your account will charge.
  The companion article has the numbers that are not simulated.
- **One token here is one whitespace-separated word.** Close enough for a
  6,000-word document, not close enough to predict a real invoice.
- **It models prefix caching only.** No batching, no reasoning tokens, no
  streaming, no router stickiness.

## Where the answers are

All answers live on the **`solusi`** branch:

```bash
git diff main solusi -- 0006.prompt-caching/
```

Read [`HINTS.md`](HINTS.md) first. It has three levels, and the first one is
enough for most people.
