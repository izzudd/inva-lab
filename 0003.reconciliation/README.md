# Lab 3 — One payment, three paths

Part of the [`inva-lab`](../README.md) repo. Every command below is run from the
`0003.reconciliation/` directory.

```bash
make up      # start the db + API + gateway (fake)
make demo    # the whole story: that night's webhooks, the morning job, the late webhook
make check   # this lab's target
```

The system has already been through the previous lab: the webhook path is idempotent. What is new is
**the second path**. If a payment's webhook never arrived — the gateway was down, we were down, or the
connection dropped mid-flight — a morning job reads the gateway's **settlement report** and closes
whatever is missing.

Two paths for the same fact. And neither path knows the other exists.

This is what happens in this lab (numbers from `make demo`, one day when the gateway was down):

| | now |
|---|---|
| 3 webhooks that night, then the morning reconciliation job | 6 payments become **9 rows** — 3 of them hold two rows, one per path |
| the late webhook finally arrives | 6 payments become **12 rows** — all doubled, balance 665,000 against the 220,000 it should be |
| the reconciliation job run twice | **6 new rows** each run, and the job reports `inserted=6` (not 0) |
| two job runs at the same time | **12 rows** for 6 payments, balance up 420,000 against 210,000 |
| a settlement row whose amount differs from what is recorded | **2 rows** for 1 payment, and `mismatched` stays empty |

## Your mission

Make `make check` green. Three conditions:

1. **One payment, one row.** From any path, and no matter how many times a path is called. Six payments
   in the report = six ledger rows, not nine, not twelve.
2. **The job can run again, and its report is honest.** A second run for the same day adds no rows and
   reports `inserted=0`. A run that only managed part of the work (`limit=2`) can be continued
   whenever, without doubling. Two overlapping runs must not double either.
3. **An amount already recorded does not change quietly.** If the settlement report states an amount
   different from what is already in the ledger, the row stays one, the amount stays the first one, and
   the difference is **reported** in the job summary (`mismatched`).

You may change anything except:

- the contract of `GET /api/accounts/:id`, `GET /api/accounts/:id/entries`, `POST /jobs/reconcile`
  (their responses are read by `make check`), and the fake gateway (`gateway/`)
- the contents of `db/init/02_seed.sql`

## Where to start

```bash
make demo        # run this first: the story, not the numbers
make settlement  # the settlement report the job reads
make entries     # ledger rows for account 1 (there is a `source` column)
make jobs        # reconciliation run history
make psql        # into the database
```

The gateway is fake and its reports are generated from the date, so the same date always produces the
same payments. Any date works: `make demo DAY=2024-03-17`.

## Before you open the answer

If you get stuck, open `HINTS.md` in order. Do not jump to hint 3.

- stuck 45 minutes → hint 1
- stuck 90 minutes → hint 2
- giving up → hint 3, and **write down where you gave up**

Do not open the `solusi` branch before you are genuinely stuck.

## Why this exists

In the previous lab, "the payment" and "the message announcing that payment" happened to always arrive
as a pair, so the difference never mattered. As soon as a second path exists, that difference becomes
the most important thing in the system: **the right key is not the unique key, it is the key owned by
the fact, not by the message.**

And the subtler second half: two paths that are each correct can need **different policies** when they
find something odd. A webhook may answer 409 for one weird event; a reconciliation job must not die
because one report line does not match.

## The limits of this lab

- **One charge = one fact.** Here a payment has only one possible content. As soon as there is a second
  event about the same charge that is genuinely new — a refund, a chargeback, a partial payment —
  `charge_id` alone is no longer enough: you need a key per (charge, kind of fact), plus a rule about
  the order of events.
- **Who wins is a business decision.** Here the rule is "whatever was recorded first wins, and the
  difference is reported". Some systems choose the opposite (last settlement wins, with an adjustment
  row). What is not allowed is choosing without realising it.
