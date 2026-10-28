# inva-lab

Practice labs for [invasikode.com](https://invasikode.com) — learn by getting stuck first, not by
reading the *happy path*.

Each lab is a small repo that **runs**, deliberately made slow or wrong in a realistic way, with a
finish line a machine can check. Your job is not to read it. Your job is to make `make check` green.

> Indonesian versions: [`README.id.md`](README.id.md) · each lab's docs sit next to the English file
> as `README.id.md` / `HINTS.id.md`.

## Labs

Directories carry a numeric prefix so the order is visible in the repo: work from the earliest,
because each lab assumes you finished the ones before it.

| Lab | Topic | Shape of the problem |
|---|---|---|
| [`0004.mutation-and-scope/`](0004.mutation-and-scope/) | Function default values, mutation vs rebinding, scope | café till: every receipt holds the same order, total Rp0 |
| [`0005.error-messages/`](0005.error-messages/) | Readable error messages, line numbers, exit codes | CSV importer: 0 of 4 bad rows reported |
| [`0001.n-plus-one/`](0001.n-plus-one/) | N+1 queries, a missing index | feed endpoint: 41 queries, 1.1 seconds |
| [`0002.idempotency/`](0002.idempotency/) | Idempotency, unique keys, lost updates | webhook: 1 event delivered 4× becomes 4 ledger rows |
| [`0003.reconciliation/`](0003.reconciliation/) | One fact from two paths, a job that may rerun | webhook + reconciliation job: 6 payments become 12 ledger rows |

Labs `0004` and `0005` are the **beginner entry point**: `python3` is all you need — no Docker, no
database, no `pip install`. The other three are production level (FastAPI + Postgres + Docker).

## How to use it

```bash
git clone https://github.com/izzudd/inva-lab.git
cd inva-lab/0001.n-plus-one     # or any lab directory
make up      # start the database + API, seed the data
make bench   # look at the numbers before changing anything
make check   # the target you have to hit
```

Labs `0004` and `0005` need none of that — just:

```bash
cd inva-lab/0004.mutation-and-scope
make demo    # see the symptom first
make check   # the target you have to hit
```

The other three need Docker. You do not have to install Python, Node or Postgres on your machine —
everything runs inside containers. Ports in use: `58000`/`55432` (lab `0001.n-plus-one`),
`58100`/`55433` (lab `0002.idempotency`), `58102`/`58103`/`55434` (lab `0003.reconciliation`).
Labs `0004` and `0005` use no ports at all.

Suggested order: `0004.mutation-and-scope`, then `0005.error-messages` (both need only `python3`),
then `0001.n-plus-one`, `0002.idempotency`, and `0003.reconciliation` — the last one assumes you
finished the idempotency lab, because its starting code is the result of that lab.

Directory names may change; the Docker project name is pinned in each `docker-compose.yml` (`name:`),
so your containers and volumes survive a rename.

## Where the answers are

All answers live on the **`solusi`** branch, split per lab directory. Do not open it before you are
stuck — if you only read it, you get the same thing a normal tutorial gives you, which is exactly
what we are trying to avoid.

```bash
git diff main solusi -- 0001.n-plus-one/
```

Every lab also ships a `HINTS.md` with three levels. Use that first.

## House rules

- **The numbers in each lab's README are measurements, not estimates.** If you change something in
  the lab and the numbers differ, that is your machine being different — report it in an issue.
- **Do not shrink the dataset** to make the target easier. The dataset is the question.
- If you give up, write down where you gave up. That is part of the exercise.

## Language

English is the primary language of this repo. Indonesian originals are kept beside each English file
as `README.id.md` / `HINTS.id.md`. The lab *code* (identifiers, comments, and the strings `make check`
prints) is still Indonesian — `LULUS` means PASS, `GAGAL` means FAIL.

## License

MIT — use it, change it, spread it.
