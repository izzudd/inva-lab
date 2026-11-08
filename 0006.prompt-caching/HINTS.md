# Hints

Open them one at a time. Each hint only gives you the next question, not the answer.

---

## Hint 1 — what is actually being hashed

`make what-changes` prints two consecutive requests, block by block. Run it.

Three questions:

1. The tools line says `DIFFERENT`. Which field inside the tool definitions differs between turn 1
   and turn 2 — and does the model need it?
2. Block `[0]` says `CHANGED`, and its word count is the same both times. So the text is not longer,
   it is *different*. What in `system_prompt()` depends on the clock?
3. The caret marks the breakpoint. On request 1 it is on block `[1]`, on request 2 it is on block
   `[3]`. The provider writes an entry **only** at the caret, so ask yourself: which prefix did turn
   1 write, and does turn 2 ever look at it?

Nothing else matters until those three questions have the same answer: **the first block of every
request must be byte-identical to the first block of the request before it.**

---

## Hint 2 — three lines, and the one that is not a line of prose

1. **The tools are part of the prefix.** The provider hashes `tools` and then the blocks, so a
   rewritten tool description invalidates everything after it, including the six thousand words of
   handbook. A "registry snapshot" timestamp in a tool definition is a timestamp in the prefix.
2. **The date has to move, not disappear.** `make check` fails check C if the prefix changes between
   two days *and* fails it again if the date never reaches the model. So the clock belongs at the
   end of the request — in the turn you are sending — not in the handbook.
3. **`make bench`, turns 3 and 4.** The token count grows by ~320 a turn, then almost nothing, then
   it drops at turn 7. `bench.py` does not print the transcript's length, but the drop is a rewrite.
   A transcript that is rewritten cannot be a prefix. Which function in `loop.py` rewrites it, and
   what would "shorten the context without touching the prefix" look like instead?

---

## Hint 3 — the shape of the fix

Four edits. None of them are in `agent/provider.py`, and none of them make the prompt shorter.

**1. `tools_for_request()` returns `TOOLS`.** The definitions are already a list in a fixed order.
A snapshot string adds nothing the model uses.

**2. `system_prompt()` takes no clock.** The handbook block becomes constant, and `build_request()`
marks it as the first breakpoint with a longer lifetime:

```python
blocks = [Block(role="system", text=system_prompt(), cache=True, ttl=LONG_TTL)]
```

`LONG_TTL` is 3,600 seconds. A cache write at that lifetime costs more per token than the 5-minute
one, but the handbook is written once and read for the rest of the hour. Check F is the turn after
the ten-minute pause: with the default 300-second TTL, that turn finds nothing and rewrites 6,135
tokens.

**3. The date travels with the turn.** In `run_ticket()`, stamp the message you append, not the
prompt you build:

```python
history.append({"role": "user", "text": f"{text}\n\n[session date {today(clock)}]"})
```

This is the difference between fixing the cache and deleting the feature. Check C tests both halves.

**4. `compress()` goes away, or it becomes an appended message.** The clean version is: append
everything, and never rewrite. If you truly need a summary, append it as a *new* block at the end —
the earlier blocks stay untouched, so the prefix still matches and a later request can still read it.
Remove the `SUMMARY_KEEP` call and check D goes green; your token count will go *up* by about 6% and
your bill will go down, which is the lesson of the whole lab.

**5. Print the measurement.** In `loop.py`:

```python
result = run_all(Provider(clock=Clock()))
print(f"summary turns={result['turns']} hit_rate={result['hit_rate']:.3f} cost_usd={result['cost_usd']:.6f}")
```

Check G re-runs the loop itself and compares your numbers with the ledger. A printed number that does
not match the ledger is worse than no number.
