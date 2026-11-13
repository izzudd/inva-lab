# Hints

Open them one at a time. Each hint only gives you the next question, not the answer.

---

## Hint 1 — the log repeats, and it does not have to

`make demo` prints forty lines that say the same thing. Read three of them, then ask:

1. The payload is `status ACTIVE -> DRAFT` every time. So the store's status was
   back to `ACTIVE` before each write — who put it there, and why is it allowed to?
2. `make demo` also renames `TEE-01`, and that costs the store forty writes. What
   in `app/sync.py` compares the payload you are about to send with
   `store.get(gid)`? Nothing does. What would "I have nothing to say" look like as
   one line of Python?
3. The store fires a webhook even when the payload changes nothing. So a write you
   did not need is not free: it produces an event, and the event produces another
   write. Which of the forty lines would survive a diff against live state?

Fix that and the log goes quiet. It also leaves a product the supplier dropped
sitting at `ACTIVE` — keep going, because that is the actual bug.

---

## Hint 2 — two rules, one field

Write both rules down, in the form each side checks them:

- the app: supplier says unavailable → `status = "DRAFT"`;
- the store: `inventory_quantity > 0` and `status == "DRAFT"` → `status = "ACTIVE"`.

Neither rule is wrong. Together, is there any state both accept? There is exactly
one — and the app never writes the field that would reach it. So each write is
corrected by the other side, and the correction is a new event.

Three questions:

1. A product that is really out of stock has no stock. If the app drafts a product,
   what should `inventory_quantity` be, and who is allowed to write it?
2. If you write `inventory_quantity = 0`, you have thrown away a number. Where does
   the app keep it so that `F` — supplier comes back — ends `ACTIVE` with the stock
   it had, and not with `0` or with a constant you invented?
3. You may be tempted to ignore the webhooks your own writes produce. Check C and
   check G would go green. Check A would not: the automation still flipped your
   field, and now nobody is listening. Suppressing the echo hides the loop; it does
   not settle who owns the field.

---

## Hint 3 — five updates, one decision

`make check`'s scenario E delivers five supplier updates before the worker runs.
The first says in stock, the fifth says gone, and the app acts on the first.

Two things make it act on the first, and they are in different places:

1. `handle_event()` drops an event when one is already queued for that product.
   Which event should survive a burst — and does the queue's data structure make
   that a one-word change?
2. `Job` carries `available`, read at the moment the event arrived. By the time
   `drain()` runs, that answer can be minutes old. What is the only moment the
   supplier's answer is worth reading?

The shape of the fix:

```python
# handle_event: the newest event is the one worth acting on
queue[gid] = Job(gid=gid)

# desired(): ask the supplier now, not when the event arrived
if not feed.available(sku_of(gid)):
    ...
```

Both halves matter for the same reason the whole lab exists: a decision is only
worth acting on against the state it will be applied to. The event tells you
*which product*; it does not tell you *what is true*.
