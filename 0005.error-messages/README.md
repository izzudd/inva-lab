# Lab 5 — A script that cannot say where it went wrong

Part of the [`inva-lab`](../README.md) repo. Every command below is run from the
`0005.error-messages/` directory.

```bash
make demo    # see what the user sees for each sample file
make check   # this lab's target
make impor FILE=data/contoh/beberapa.csv   # run the importer once
```

You have a small script: `app/impor.py` reads a `.csv` of registrants (`nama,email,umur`) and stores the
valid rows. While you build the file yourself, everything is fine. The moment the file comes from
another team, the phone starts ringing:

- **Some files kill the script with a `Traceback` on screen**, and only the line that happened to trip
  it first gets reported — the rest are never mentioned.
- **Other files do the opposite: no complaint at all**, even though they clearly contain a broken row.
- **The people asking for help complain**: "I don't know which line is wrong, which column, or what I'm
  supposed to do." The traceback names Python variables, not lines in their file.

This is what happens in this lab (numbers from `make demo` and `make check`, run as-is):

| command | what appears now |
|---|---|
| `make impor FILE=data/contoh/beberapa.csv` | `ValueError: invalid literal for int() ... 'dua puluh'` — **0 of 4** problems reported |
| `make impor FILE=data/contoh/kosong.csv` | no complaint, and it says `3 baris diimpor`, exit code `0` |
| `make impor FILE=data/contoh/kolom.csv` | `IndexError: list index out of range` — **0 of 2** problems reported |
| `make impor FILE=data/contoh/tidak-ada.csv` | `FileNotFoundError`, exit code `1` |
| `make check` | **1 of 7** checks green (only A) |

## Why this lab differs from 0001–0003

Labs 0001 to 0003 are production level: FastAPI, Postgres, Docker, and performance targets. This lab is
deliberately beginner level, for readers of the **Programming Fundamentals** series: standard **Python
3 only**. **No Docker**, **no database**, nothing to `pip install` — it runs with whatever `python3` you
have (tested with Python 3.12.3). What you practise here is not speed or concurrency, but one thing that
applies to every language: **making a program's failures readable by humans.**

## Your mission

Make `make check` green. Seven checks (A–G) in `scripts/check.py`, one theme:

> A useful error message answers three things: **where**, **what is wrong**, and **what it should be**.
> A program that stops at the first problem answers one.

The three big conditions:

1. **Report everything, do not die on the first.** For a file with four problems, all four are reported —
   and no Python `Traceback` leaks to the user. A clean file complains about nothing.
2. **Every report says where and what.** The line number **in the file** (not the data index), the bad
   column's name, the bad value, and what was expected. One problem = one line, in this format:

   ```
   baris <nomor>: <kolom> — <apa yang salah, nilainya, dan yang diharapkan>
   ```

3. **The exit code distinguishes three states**, not one code for everything: `0` = done, `1` = some rows
   are broken, `2` = used wrongly (file missing, argument missing).

You may change `app/` however you like. What you **must not** change: `scripts/check.py` (the grader),
`data/` (the fixtures, including `data/contoh/`), and the `Makefile`.

## Where to start

```bash
make demo     # the story first: what the user sees for each file
make bantu    # list the commands
```

The sample files are deliberately small and broken in different ways:

- `data/contoh/kosong.csv` — contains a row with no name
- `data/contoh/beberapa.csv` — several broken rows at once, one of them with two problems
- `data/contoh/kolom.csv` — contains rows whose column count does not match the header
- `data/pendaftar.csv` — a clean file, for comparison

## Before you open the answer

If you get stuck, open `HINTS.md` in order. Do not jump to hint 3.

- stuck 20 minutes → hint 1
- stuck 40 minutes → hint 2
- giving up → hint 3, and **write down where you gave up**

Do not open the `solusi` branch before you are genuinely stuck.

## Why this exists

When a beginner writes a validator, what gets skipped most often is not the validation — it is the
report. The code does `raise ValueError` and assumes Python's message is enough. On your own laptop it
is. In someone else's hands, `ValueError: invalid literal for int() with base 10: 'dua puluh'` does not
say **which line of the file** is broken. The error message is the only part of a program that a
panicking person reads. Writing it is not extra work; it is the work.

## The limits of this lab

- **Every error here is "wrong data", not "wrong program".** You are validating input. Errors caused by
  a bug in your own code (a logic mistake) are a different story.
- **This is a one-shot program, not a service.** The exit code matters because scripts get called from
  `cron`, `make`, or a pipe; inside a service, "where" can mean a field in the request body rather than
  a line number.
- **It does not scale yet.** The format `baris N: kolom — pesan` is enough for files this size. At
  hundreds of megabytes, reporting everything at once has its own cost.
