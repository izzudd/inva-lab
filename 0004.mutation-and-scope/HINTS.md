# Hints

Open them one at a time. Each hint only gives you the next question, not the answer.

---

## Hint 1 — why table 3 gets table 1's order

Run `make demo`. Three tables open, each orders one item. Look at the contents of all three receipts:
they hold the same items, even though they are different tables.

Focus on one function first: `pesanan_baru`. Questions:

1. Where does the item list inside one receipt come from? Where is it created, and how many times?
2. Is a Python parameter's default value computed **once** when the function is defined, or on every
   call? Prove your answer: call `pesanan_baru(1)` twice, then check
   `pesanan_baru(1)["item"] is pesanan_baru(2)["item"]`.
3. If the answer is "the same object forever", why did the original author write `item=[]`? Did they
   realise the difference?

---

## Hint 2 — the receipt that says its total is Rp0

Get group 1 green first, then move on. Now look at `make check` again: group 2 is still red, and each
receipt's `total` stays Rp0 even though the items are now correct.

Focus on `tambah_item`. Questions:

1. What does `total = pesanan["total"]` do? Does `total` there point at the same object as
   `pesanan["total"]`, or does it merely copy the value?
2. The next line, `total = total + harga * qty` — what changes there: `pesanan`, or only the local name
   `total`?
3. After `tambah_item` returns, which `total` will whoever holds `pesanan` see? Why?

What you must not forget: the same variable name in two places is not necessarily the same object.

---

## Hint 3 — three decisions

All one theme: **first write down on paper which object you are changing, then touch the right name.**

**1. `pesanan_baru` must not have a list as its default value.** A default is computed once and reused
forever. Change it to `item=None`, then inside the function:

```python
if item is None:
    item = []
```

`if item is None` beats `item or []` here: `item or []` also makes a new list when the caller
deliberately passed an empty list, so it is right in this demo and wrong in other cases.

**2. `tambah_item` has to write back into the receipt, not into a local name.**

```python
pesanan["total"] = pesanan["total"] + harga * qty
```

The difference is subtle: `total = pesanan["total"]` copies a **value**; `pesanan["total"] = ...`
changes the **object** the caller holds. The local name `total` dies when the function returns.

**3. `catat_penjualan` must tell Python that `TOTAL_KAS` belongs to the module.**

```python
global TOTAL_KAS
TOTAL_KAS = TOTAL_KAS + jumlah
```

Without `global`, assigning to `TOTAL_KAS` inside the function makes Python treat it as a new local
variable. Write `TOTAL_KAS = TOTAL_KAS + jumlah` without `global` and you get `UnboundLocalError` —
which is actually better, because the error is visible. The original author avoided it by routing
through another variable named `total`, and that is what made this bug silent.

---

## The traps to avoid

**Fixing only one layer.** The first three labs in this repo already trained this: fixing one problem is
not enough, `make check` stays red because the layers are different. Hints 1 to 3 point at three
different places.

**"Safeguarding" with copies.** The temptation: add `.copy()` everywhere so nothing overwrites anything.
But `.copy()` only makes a new container — if its contents are mutable too, your copy still shares them
with the original. Before adding a copy, ask: do I want to separate the container or the contents?

**Renaming variables so they "differ".** If you rename `total` to `total_nota` inside `tambah_item`,
the bug does not disappear, it just changes name. The name was never wrong; what was wrong is that you
changed a local name instead of the value inside the dict.

**Deleting items from the leaked list so it "looks clean" at the end.** That patches the symptom in
`demo`, not in `kasir.py`. `make check` calls `kasir.py` without going through `demo`, so it stays red.
