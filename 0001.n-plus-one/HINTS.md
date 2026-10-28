# Hints

Open them one at a time. Each hint only gives you the next question, not the answer.

---

## Hint 1 — where those 41 queries come from

Forty-one queries. Group the number before changing anything.

There are three groups. One for the post list. Two more, each appearing once per post you process —
which means both are inside a loop.

Once you find them, do not fix both at once. Answer this first: **of those two groups, which one is
actually making it slow?** One is far more expensive than the other. Guess wrong and you will fix the
cheap one, see almost no change, and get confused.

A hint for deciding: compare which column each group searches on. One group looks things up by
primary key — the cheapest search a database can do. The other searches on an ordinary column.

---

## Hint 2 — the query count is 2, so why is it still red

Congratulations, you are down to 2 queries. Now look at the second line of `make check`: still around
60 ms, against a 30 ms target.

Few queries. So the problem is not the count.

Answer this outside the application:

```bash
make psql
```

```sql
EXPLAIN ANALYZE SELECT count(*) FROM comments WHERE post_id = 7;
```

Watch two things: what kind of scan it is, and how many rows it reads to produce one number.

750,000 rows read to answer one simple question, "how many comments does this post have". The next
question: why does Postgres read that far when you only asked for one number?

---

## Hint 3 — two fixes, in two different places

There are **two** things that must change, and neither is in the same file.

**1. In the application.** The last remaining query, the one counting comments, runs once per post.
You do not need the rows at all — you need the number. Collect every post id on the page, then fetch
all the numbers in **one** grouped query (`GROUP BY`).

At this point: 2 queries, but `make check` is still red on the latency line.

**2. In the database.** `comments.post_id` has no index. This is the part most often skipped,
because "the code is correct" — and it is correct, the data is what is wrong.

In production `comments` will never be empty, so the index has to be created without locking the
table:

```sql
CREATE INDEX CONCURRENTLY idx_comments_post_id ON comments (post_id);
```

Why `CONCURRENTLY` matters, and what it costs — that is a question for the next lab.

---

## The trap to avoid

The fastest way to get the query count to 2 is to eager load the comment relation and then call
`len()` on it. It feels like the right answer, because *eager loading* is the fix written in almost
every article about N+1.

The query count drops to 2 immediately. But look at `make check`: **still ~1,000 ms.**

What happens: 20 posts × ~1,875 comments = **37,500 rows** moved from the database into application
memory, just so Python can count them with `len()`. The database stops working hard; now the
application does. Adding an index does not help either — the data still has to cross.

Counting does not need the data. It needs the number.
