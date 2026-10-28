# Lab 2 — One payment, four ledger rows

Part of the [`inva-lab`](../README.md) repo. Every command below is run from the `0002.idempotency/`
directory.

```bash
make up      # start the db + API
make replay  # replay one event, the way the gateway does
make check   # this lab's target
```

`POST /webhooks/payments` receives payment notifications from the gateway. On a laptop, with three
accounts and two events, this endpoint runs smoothly: one request in, one ledger row out, balance up.
Nothing looks wrong — and indeed the code is not wrong.

What you cannot see: **HTTP has no way to tell the sender that our answer arrived.** The gateway sends
an event, we commit the transaction, then the answer is lost on the way back — connection dropped,
load balancer timed out, our container restarted a second too early. From our side everything is
done. From the gateway's side the event was never received, so it sends again. And again tomorrow.

That is not a broken gateway. It is the only option it has, and it chooses **duplicate over lost** —
because losing a payment costs more than repeating one. The duplicate becomes your work.

This is what happens in this lab:

| | now |
|---|---|
| one event redelivered 4× | **4** ledger rows for 1 event, balance up **4× the amount** |
| one event delivered 30× at once | **30 rows**, and the balance only partly rises (on the lab author's machine: 40,000–60,000 out of the 300,000 it should be) |
| 3 different events, each delivered 2× | **6 rows**, balance up **6× the amount** |
| the exact same request sent 2× | **2 rows** — nothing in the database can tell which one was already processed |

## Your mission

Make `make check` green. Four conditions:

1. **Exactly once.** One event is applied exactly once. Not doubled, nothing lost: three different
   events stay three ledger rows, not six, not two.
2. **A redelivery is answered like the first response.** Not an error, not an "already processed"
   message — the same body, with the same `entry_id`. This also holds when the redelivery arrives
   concurrently. The reason is not politeness: an answer recomputed from the database **as it is
   now** can be wrong, because other events have moved the balance. The correct answer is the first
   attempt's answer, as-is.
3. **A reused `event_id` with different content is not processed.** A different amount for the same
   event must not reach the ledger.
4. **The balance stays correct when many events arrive at once.** Thirty *different* events arriving
   together must raise the balance thirty times the amount, not twice. This comes from the second
   complaint, not the first: a merchant ended up with less than they should, and the gateway was not
   at fault.

You may change anything except:

- the response shape of `GET /api/accounts/:id` and `GET /api/accounts/:id/entries` — that is your
  measuring instrument, and `make check` reads it
- the contents of `db/init/02_seed.sql`

## Where to start

```bash
make replay    # 4 deliveries for one event, then two numbers below it
make entries   # balance + every ledger row for account 3
make psql      # into the database
make logs      # API logs, if something is answering with an error
```

## Before you open the answer

If you get stuck, open `HINTS.md` in order. Do not jump to hint 3.

- stuck 45 minutes → hint 1
- stuck 90 minutes → hint 2
- giving up → hint 3, and **write down where you gave up** — that is part of this lab, not a failure

Do not open the `solusi` branch before you are genuinely stuck.

## Why this exists

Idempotency is not about "adding a check". It is about deciding **who is entitled to decide** whether
something already happened: your application, or the database.

This lab has two bugs and one trap, and all three exist because that decision was made in the wrong
place. The first one only becomes visible *after* you fix the bug, not before — and that is where
"duplicate key value violates unique constraint" shows up, which may already be familiar to you.

The starting code looks correct, deliberately. Part of it was written with good intentions, complete
with a comment explaining why that part exists. Read the comment slowly: it is the only guard this
endpoint has, and it is a guard in the wrong place.

## The limits of this lab

Two things are **not** here, on purpose, and both are harder than what is.

- **Side effects outside the database.** If your handler also sends email or calls a third-party API,
  "put it in one transaction" does not help: email cannot be rolled back. That is the outbox pattern,
  and it is not this lab.
- **A fact arriving from two paths.** Here one payment has exactly one path: the gateway webhook. As
  soon as a reconciliation job closes payments whose webhook was late, every key you use in this lab
  stops working — and the only one that keeps working is the key that comes from the domain itself
  (the payment reference), not from the transport. That is the next lab.
