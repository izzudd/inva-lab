# Lab 4 — Every receipt in this café lists the same order

Part of the [`inva-lab`](../README.md) repo. Every command below is run from the
`0004.mutation-and-scope/` directory.

```bash
make demo    # the story: three tables order, look at the receipts
make check   # this lab's target
```

A busy night. The barista opens three tables, each table orders one item. Then the barista reports:
**every table's receipt holds the same items** — coffee, tea, bread, all three — even though each table
ordered one thing. And every receipt says the total is **Rp0**. The daily till at the end is Rp0 too,
despite a full night of sales.

This is what comes out when `make demo` runs on the machine this lab was built on:

| | now |
|---|---|
| three tables (1, 3, 5), each ordering one item | every receipt holds **the same 3 items**: `kopi x2, teh x1, roti x1` |
| each receipt's total | **Rp0** (table 1 should be Rp30,000, table 3 Rp8,000, table 5 Rp12,000) |
| daily till after three tables of sales | **Rp0** (should be Rp50,000) |
| `make check` | **6 of 6** checks red |

No errors, no exceptions. The code runs to completion, and every function looks sensible at a glance.
The problem is not in one place — there are three, and each has a different cure.

## This lab is different from the previous three

Labs `0001`–`0003` run on FastAPI + Postgres + Docker. This one does not. It needs only **standard
Python 3** — no Docker, no database, no `pip install`.

The reason: this lab is for readers of the **Programming Fundamentals** series, who may be new to
Python and do not have Docker on their machine. If you have to install Docker before you can start
learning, you stop at step zero. So here you need exactly one thing: `python3`, which exists on almost
every machine. All the code is in one file, `kasir.py`.

## Your mission

Make `make check` green. Three conditions:

1. **Each receipt holds only its own table's order.** A table that has not ordered yet keeps an empty
   receipt. Two tables with different orders must not swap contents.
2. **Each total is computed from its items.** Item count and qty multiply, instead of staying at Rp0.
3. **The daily till rises by what was actually sold.** Sell Rp32,000 → the till rises Rp32,000.

You may change anything in `kasir.py`, as long as its three public functions can still be called the
way they are called now — `pesanan_baru(meja)`, `tambah_item(pesanan, nama, qty=1)`, `total_kas()`. The
`MENU` name is used by `make demo` too. `make check` calls all three exactly like that.

## Where to start

```bash
make demo    # the story, not the numbers
make check   # see for yourself which checks are red
```

Then open `kasir.py` and read from the top. Every function has a comment explaining its author's
intent. The intent is good. Find out why good intent still produces the wrong receipt.

## Before you open the answer

If you get stuck, open `HINTS.md` in order. Do not jump to hint 3.

- stuck 30 minutes → hint 1
- stuck 60 minutes → hint 2
- giving up → hint 3, and **write down where you gave up**

Do not open the `solusi` branch before you are genuinely stuck.

## Why this exists

Most people learn "functions" from examples that get called once. In reality functions get called
repeatedly, and the two things rarely taught alongside that are exactly what breaks this lab:

- **A function's default value is computed once, not per call.** If the default is a mutable object (a
  list, a dict), that object is shared with every caller — forever.
- **Writing `x = ...` inside a function only touches the name `x` in that function.** If what you mean
  to change lives outside (inside a dict, or in module scope), you have to touch the right object or
  the right name.

Both look trivial while you read them, and both only show up when the code is used more than once.
That is the difference between reading a tutorial and getting stuck yourself.

## The limits of this lab

- **This is not a lesson about classes.** Here all the state is a dict and a module variable. The real
  world often solves problems of this shape with a class — but a class is just another name for the same
  thing: you still have to know which object you are holding and which one you are changing.
- **A global variable is not always the right answer.** In this lab a global `TOTAL_KAS` is the simplest
  shape. Once more than one till runs at the same time, one global variable is not enough — and that is
  another lab's story.
- **A wrong default value is not the only "computed once" trap.** The same applies to caches,
  connections, and anything built when the module is first imported.
