# Hints

Open them one at a time. Each hint only gives you the next question, not the answer.

---

## Hint 1 — why 4 rows when this is one payment

Run `make replay`. Four deliveries, one event, one row that should exist.

The first question is not "where is the bug" — there is no bug in that code. The first question is:
**why does the gateway redeliver?**

The answer is in their docs, roughly: "if we do not receive a 2xx answer, we send it again". Now the
second question, the important one: your first attempt was answered with 200. So **why do they not
know that?**

Try to answer before moving on. If you cannot, you do not yet know where the problem is — you only
know something is wrong. (The only two lines you need to look at: `session.commit()`, and the
`return` after it.)

Third question: if redelivery is normal and nobody's fault, **who should decide that this event was
already received?** And where does that decision live until tomorrow?

---

## Hint 2 — you added the unique key, and now it is noisy

Once you give the database authority to decide (a unique key on the right column), `make check` — which
was red in several places — produces something new: API logs full of `duplicate key value violates
unique constraint`, and redeliveries answered with **HTTP 500**.

Notice what happened in the database then: still one row, balance still correct. So the duplicates
are solved — what remains is this: the gateway receives an error, and since it never knew the answer
arrived, it will redeliver. Again, and again, until the endpoint is considered dead on their side.
Your logs are full, and not one line in them means "we already received this".

Three questions, and answer all three before writing code:

**(a) If one statement inside a transaction fails, what happens to that transaction and to the next
statement?** Do not answer from memory. Prove it in `make psql`:

```sql
BEGIN;
INSERT INTO ledger_entries (account_id, event_id, delivery_id, amount)
    VALUES (1, 'evt_seed_01', 'dlv_coba_1', 1);   -- this event_id already exists
SELECT 1;
ROLLBACK;
```

Look at the second error. The code is `25P02`, and that name is worth knowing.

**(b) We just treated "this event already exists" as a failure. Why?** The gateway redelivers because
it **got no answer** — it genuinely does not know whether its first attempt worked. So what is the
correct answer for the second attempt?

**(c) If the second attempt must be answered exactly like the first, where do you keep that first
answer?** Look again at what check group C in `make check` demands.

---

## Hint 3 — four decisions, and where each one is made

All one theme: **something that must happen exactly once has to be decided by the database, inside the
same transaction as the work.**

**1. Claim the event, do not check-then-write.** `SELECT` first, then `INSERT`, can always lose a race
— and that is not theory, see checks D and G. One statement
`INSERT ... ON CONFLICT DO NOTHING ... RETURNING` can do "check and write" as one operation nothing
can interrupt. An empty `RETURNING` means you lost the race, and that answer is as valid as winning.

**2. A conflict is not an error.** The "already processed" branch must run normally, not through an
`except`, and the answer is the first attempt's answer that you stored.

**3. The claim and the work are one transaction, committed once.** If you store the claim first and
commit, there is a gap where the server may die: the event is recorded as processed while the ledger
row and balance never existed — and every redelivery after that is treated as a duplicate. Duplicates
you can see. Loss you cannot.

**4. The balance is not an idempotency problem, but it lives in the same lab.** Why is check G2 red
when only 20 ledger rows went in, and why is `account.balance = account.balance + amount` in Python
not the same operation as `SET balance = balance + amount` in SQL?

---

## The trap to avoid

After the unique key is in place, the fastest way to make the log errors disappear is:

```python
try:
    session.flush()
except IntegrityError:
    pass
```

It feels right, because the result is indeed "no duplicate row". Two things happen next:

**The transaction is already dead.** In Postgres a failed statement aborts the whole transaction. Any
statement after an unhandled `IntegrityError` fails with `25P02` ("current transaction is aborted"). If
you swallow that error and continue, the rest of the work in that request **does not run** — and if
you return HTTP 200, you just said "done" for work that never happened.

**If you do want to handle it, you need a `SAVEPOINT`** so the rollback is limited to that one
statement.

Which is why hint 3 points you at `ON CONFLICT DO NOTHING`: not as a trick to silence the error, but so
that there is never an error to handle. A predictable conflict is not an exception.
