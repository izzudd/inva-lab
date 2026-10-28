# Lab 1 — A feed endpoint that runs on your laptop and falls over in production

Part of the [`inva-lab`](../README.md) repo. Every command below is run from the `0001.n-plus-one/`
directory.

```bash
make up      # start the db + API, seed 400 posts and 750,000 comments
make bench   # look at the numbers yourself
make check   # this lab's target
```

`GET /api/posts?limit=20` returns the 20 latest posts with each one's author name and comment count.
On a laptop with dummy data this endpoint looks unremarkable, and nothing about the code looks wrong.

Here:

| | now |
|---|---|
| queries to the database per request | **41** |
| p95 latency | **~1,100 ms** |

The server is not erroring. It is not slow only in certain cases. It is consistently slow on every
request — which is exactly why the problem never shows up in staging, because staging is empty.

## Your mission

Make `make check` green:

- queries per request **≤ 3**
- p95 latency **≤ 30 ms**

One condition is not negotiable: **the result has to stay the same.** Compare the response body
before and after your change. If the comments that should be 1,875 become 0, you are not done — you
only moved the problem.

You may change anything except:

- the response contract (`id`, `title`, `author`, `comment_count`)
- the size of the data in `db/init/02_seed.sql` — this dataset is the question, not a variable

## About that 30 ms

It is this lab's budget, not a law of nature. The number was chosen so that *both layers* of the
problem in this endpoint have to be fixed — fix only one and a line in `make check` stays red, which
is the whole point.

So you do not have to take it on faith: this endpoint's cost has been measured at two dataset sizes.
300,000 comment rows → 36 ms. 750,000 rows → 60 ms. Nearly proportional to row count, not constant. If
you want to prove it yourself, multiply the seed by 3, run `make reset`, then `make bench` again.

## Where to start

Look at the `X-Db-Query-Count` header on every response. That is your measuring instrument.

```bash
make explain   # one request, just the query-count header
make psql      # into the database, for EXPLAIN ANALYZE
```

If you have never used `EXPLAIN ANALYZE`, now is the time. But do not use it blindly: write down your
guess first, then compare it against reality.

## Before you open the answer

If you get stuck, open `HINTS.md` in order. Do not jump to hint 3.

- stuck 45 minutes → hint 1
- stuck 90 minutes → hint 2
- giving up → hint 3, and **write down where you gave up** — that is part of this lab, not a failure

Do not open the `solusi` branch before you are genuinely stuck.

## Why this exists

In a tutorial you build an endpoint, the data is 20 rows, the response takes 8 ms, done. In
production the same code runs over hundreds of thousands of rows, and what shows up is not an error —
just a latency number creeping up until someone complains.

This lab has one thing tutorials do not: **the starting code looks correct.** Part of it is
deliberately written with good intentions. Find out why good intentions still produce 41 queries and
1.1 seconds.

## Companion reading

- The story version: **[Two Queries Left, Still One Second](https://invasikode.com/p/query-tinggal-2-tapi-response-masih-1-detik)**
- The answer is also on the site, in the **[Lab](https://invasikode.com/s/lab)** series — but on
  purpose you can only reach it from the link at the end of the problem article. Land there first and
  the site will send you back. Try it.
