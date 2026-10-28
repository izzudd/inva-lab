# Hints

Open them one at a time. Each hint only gives you the next question, not the answer.

---

## Hint 1 — two rows for one payment, and both feel correct

Run `make demo`. Look at the `source` column on each row: one row came from `webhook`, the other from
`recon`. The payment is the same — the `charge_id` is the same — but what distinguishes them on the two
paths is not the payment.

Three questions:

1. Which key does the webhook path use to decide "I already recorded this"? Which key does the
   reconciliation path use? Open `api/app/ledger.py` and compare the two functions in it.
2. Of those two keys, which one comes from **the payment**, and which comes from **the message
   announcing it**?
3. What happens to a key that comes from the message once a second path exists? And why must the
   reconciliation path mint its own key instead of reusing the webhook path's?

---

## Hint 2 — the job itself is not safe to rerun either

Run `make check`, then look at check C. The job is run again for the same day, and it reports
`inserted=6` — not `0`.

Questions:

1. Look at the claim key that `record_from_settlement` builds in `ledger.py`. Which part of that key
   changes on every run? And why did the author put that part in there (hint: read the comment, and see
   which rows in `ledger_entries` are filled from it)?
2. If the key no longer carries the run id, what else does this job need so two overlapping runs do not
   overwrite each other? *(The answer "nothing" is valid — try to prove why.)*
3. Look at `mismatched` in the job summary: always `[]`, even though check F prepares a report with a
   different amount. Where does that information live? Who is supposed to compare it?

---

## Hint 3 — four decisions

All one theme: **the right key is the key owned by the fact, and the policy for handling oddities
differs per path.**

**1. The claim becomes a claim about the payment, not the message.** Replace the `processed_events`
table with a claim keyed by `charge_id`: `payment_claims(charge_id, ...)`. That key is identical for the
webhook path and the reconciliation path, because both are talking about the same payment. `event_id` is
still stored, but as a trace of the first message that announced it — not as the arbiter.

**2. The unique constraint in the ledger moves too.** A unique `ledger_entries.event_id` means nothing
once the key moves; what must be unique is `charge_id`. On a production database this is a migration to
do carefully: existing duplicates have to be cleaned up first.

**3. Two paths, two policies when the claim already exists.**
- **Webhook** (previous lab): answer with the stored first response. Different content → 409, because
  the sender is still waiting for an answer.
- **Reconciliation job**: never fail the whole run because of one line. Already there and matching →
  skip silently. Already there but a different amount → **report** it in `mismatched` (say, the list of
  `charge_id`s), do not overwrite, do not add a row. A job where one bad line fails the whole day is a
  job that never completes.

**4. Once those two are done, overlapping and interrupted runs finish on their own.** No cursor, no
progress table, no run id in the key: replaying a whole day is safe, because every payment claims
itself. That is why checks E and G go green without you writing a line for them.

---

## The traps to avoid

**Giving the second path its own table.** This is the most tempting one: leave the webhook claim as it
is, and build a claims table for the job. The result is what you have now — two paths, two tables, two
truths. What has to be unified is **the key**, not the tool.

**Trusting the settlement report as the truth.** The report is also just a claim: its amount can differ
from what we already recorded, and lines can appear twice if the gateway resends its report. A job that
writes whatever it sees will write three times for one payment on the third day.

**Answering with an error so the job "stops and is visible".** A job that dies on the first bad report
line stops there forever. A line that does not match gets reported, not turned into a reason to stop.
