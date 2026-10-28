# Hints

Open them one at a time. Each hint only gives you the next question, not the answer.

---

## Hint 1 — the script dies on the first bad line

Run `make demo`. Look at the two broken files: one stops with `ValueError`, the other with `IndexError`.
And `data/contoh/kosong.csv` says nothing at all.

Three questions:

1. Open `app/impor.py`. What happens at `umur = int(baris[2])` when the contents are not a number? Who
   catches it? If nobody does, what makes the whole program stop — and how many problems never get
   reported because of it?
2. Read the comments inside `periksa` and inside the loop. Both explain a deliberate decision. Are those
   reasons still true if what you want is to report every bad row instead of stopping?
3. Now `data/contoh/kosong.csv`: why does `make impor` calmly say `3 baris diimpor` while there is a row
   with no name? Which column gets checked, and which one gets skipped?

Only one thing has to change first: **one bad row must not stop the whole run**, and **every problem has
to become one report line**, not a traceback.

---

## Hint 2 — the right "where", and the exit code

Once every problem is reported, the next two traps are the ones people hit most:

1. **The line number.** If you count from the data rows (`enumerate(data, start=1)`), that number is
   **not** the line number in the file. Line 1 of the file is the header. Open
   `data/contoh/beberapa.csv` in an editor: which line is the first problem on? Compare with what your
   program reports. Off by one means you are counting data indices, not file lines.
2. **`IndexError` in `data/contoh/kolom.csv`.** A row with too few or too many columns cannot be checked
   column by column — before touching `baris[2]`, confirm the column count is actually right.
3. **The exit code.** Right now `FileNotFoundError` also produces exit code `1`, the same as a file full
   of bad data. To a caller, "the file is not there" and "the file is there but something in it is wrong"
   are very different things. Which is `0`, which is `1`, which is `2`?

---

## Hint 3 — the final shape

All one theme: **one problem = one line, with three parts** (where, what, what it should be), and **the
program does not stop even when a row is bad**.

**1. Validation becomes a function that collects instead of throwing.** Make `periksa(baris)` return a
**list** of problems, not print or `raise`. A correct row returns an empty list. One row may hold more
than one problem (see line 3 of `beberapa.csv`: empty name **and** an email with no `@`).

**2. Check the column count first.** If `len(baris) != len(KOLOM)`, that is one problem in the
`jumlah kolom` column — and stop with that row only, because the columns cannot be trusted individually.
For other problems, `umur` is different: `int(umur)` can throw `ValueError`, so wrap it in `try/except`
and turn it into a message like `'"dua puluh" bukan angka — isi dengan bilangan bulat, misalnya 25'`.

**3. Take the line number from `enumerate(pembaca, start=2)`.** Start at 2, because line 1 of the file is
the header. That is what makes check D green.

**4. Write the report to `stderr` in a fixed format** (`baris {nomor}: {kolom} — {pesan}`), then
`return 1` if there were problems, `0` if not. For a missing file or missing argument, write one line of
explanation then `return 2` — do not let a traceback appear.

---

## The traps to avoid

**Wrapping everything in one big `try/except` in `main`.** That does remove the traceback, but it also
stops the program at the first bad line — check C stays red. What is correct: small, specific
`try/except` where failure is genuinely possible (`int(umur)`, `open(path)`), and let the rest keep
running.

**Copying Python's message verbatim.** `invalid literal for int() with base 10` is technically accurate
and useless to the user. What the user needs: which line, which column, what the value is, and how it
should be filled.

**Forgetting that one row can hold two problems.** If `periksa` returns after the first problem, line 3
of `beberapa.csv` yields only one report, and check C goes red.
