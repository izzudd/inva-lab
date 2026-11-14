# Hints

Open them one at a time. Each hint only gives you the next question, not the answer.

---

## Hint 1 — two lines, one row

`make run` prints eleven lines. Look at lines 2 and 3:

```
 2  e-104  MUG-01  set    6  @10:10  applied   MUG-01 = 6
 3  e-102  MUG-01  set    4  @10:05  applied   MUG-01 = 4
```

The message that arrives second describes 10:05. The message before it describes 10:10. Which of the
two is news, and which one is history arriving late?

Now the same question for CAP-03: every one of its five lines moves the row, including the last one,
which happens after the shelf was already counted at zero. Which line should have been refused?

---

## Hint 2 — the row needs to remember when it was true

1. **The store keeps a quantity per SKU and nothing else.** `self.rows[sku]` already has an
   `event_time` field, and `apply()` overwrites it on every message. Two messages, one field: the
   store knows the value of the last message it applied, not the time of the newest fact it holds.
   What would it have to compare before it writes?
2. **`sale` subtracts without looking.** There is one line in the sale branch, and it does not ask
   whether the shelf can cover the sale. Check C runs a small queue of its own (`one item, then two
   sales`), so it does not care what `data/messages.json` says.
3. **Nothing records what has already been processed.** Check D delivers `e-302` twice and expects
   the stock not to move. What in a message identifies *the event* rather than its content?

---

## Hint 3 — one guard, in the right order

`apply()` needs three questions before it writes, and the order matters:

1. **Have I seen this `event_id` already?** If yes, reject: the same news twice is one fact.
2. **Is the message older than the row's `event_time`?** If yes, reject and count it as stale. That is
   the guard that turns "the last message wins" into "the newest fact wins".
3. **Is this a sale larger than what the shelf holds?** If yes, reject. A sale is not a `set` with a
   minus sign, because a `set` describes a state and a sale describes an amount that must exist.

After those three, the write is the same line it was before. Then the counters in `summary()` have to
be real: `applied` is what you wrote, `rejected` is what you refused, and their sum has to be every
message you read. Check E compares that line against the store's own counters, so a summary that
counts everything as applied fails once you start refusing things.

If `make check` says `B` is still red, look at what `clock()` does: comparing the strings directly
works for this data file and breaks the day a message carries a timezone offset.
