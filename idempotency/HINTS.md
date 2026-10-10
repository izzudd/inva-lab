# Hints

Buka satu per satu. Tiap hint cuma kasih pertanyaan berikutnya, bukan jawabannya.

---

## Hint 1 — kenapa 4 baris, padahal ini satu event

Jalankan `make replay`, lalu baca dua baris teratas di outputnya: `X-Event-Id` dan
`X-Delivery-Id`.

Empat pengiriman. Satu id tetap sama di keempatnya, satu id berubah tiap kali. Tanya
diri sendiri: **kenapa gateway mengirim yang berubah-ubah, dan apa yang sebenarnya sedang
diberitahukan ke kamu?**

Sekarang balik ke `api/app/handlers.py` dan lihat penjagaan yang dipakai. Dari dua id itu,
yang mana yang dipakai untuk memutuskan "sudah pernah diproses"?

Dan satu pertanyaan yang lebih penting dari keduanya: waktu kamu mengetes endpoint ini sendiri
dengan mengirim request yang sama dua kali, kenapa hasilnya benar? Kalau kamu tidak bisa
menjawab ini, kamu belum tahu di mana bugnya — kamu cuma tahu ada yang salah.

---

## Hint 2 — sudah kamu pasang unique key, sekarang malah ribut

Sesudah kamu memberi database wewenang memutuskan (unique key di kolom yang benar), `make
check` yang tadinya merah di beberapa tempat sekarang menghasilkan hal baru: log API penuh
`duplicate key value violates unique constraint`, dan pengiriman ulang dijawab **HTTP 500**.

Perhatikan apa yang terjadi di database waktu itu: barisnya tetap satu, dan saldonya tetap
benar. Jadi dobel-nya sudah beres — yang tersisa cuma ini: gateway menerima error, dan
karena dia memang tidak pernah tahu jawabannya sampai, dia akan mengirim ulang. Lagi, dan
lagi, sampai endpoint ini dianggap mati di sisi mereka. Log-mu penuh, dan tidak ada satu pun
baris di dalamnya yang berarti "kami sudah pernah menerima ini".

Tiga pertanyaan, dan jawab ketiganya sebelum menulis kode:

**(a) Kalau satu statement di dalam transaksi gagal, apa yang terjadi pada transaksi itu
dan pada statement berikutnya?** Jangan dijawab dari ingatan. Buktikan di `make psql`:

```sql
BEGIN;
INSERT INTO ledger_entries (account_id, event_id, delivery_id, amount)
    VALUES (1, 'evt_seed_01', 'dlv_coba_1', 1);   -- event_id ini sudah ada
SELECT 1;
ROLLBACK;
```

Lihat error kedua. Kode errornya `25P02`, dan itu nama yang perlu kamu tahu.

**(b) Tadi kita menganggap "event ini sudah ada" sebagai kegagalan. Dari mana?** Gateway itu
mengirim ulang karena dia **tidak mendapat jawaban** — dia memang tidak tahu percobaan
pertamanya berhasil atau tidak. Jadi apa jawaban yang benar untuk percobaan kedua?

**(c) Kalau percobaan kedua harus dijawab persis seperti percobaan pertama, di mana kamu
menyimpan jawaban pertama itu?** Lihat lagi apa yang dituntut pemeriksaan C di
`make check`.

---

## Hint 3 — empat keputusan, dan di mana masing-masing diambil

Semuanya satu tema: **hal yang harus terjadi tepat sekali harus diputuskan oleh database,
di dalam transaksi yang sama dengan pekerjaannya.**

**1. Klaim eventnya, jangan memeriksa dulu lalu menulis.** `SELECT` dulu, baru `INSERT`,
selalu bisa kalah balapan — dan itu bukan teori, lihat `make check` D dan G. Satu statement
`INSERT ... ON CONFLICT DO NOTHING ... RETURNING` bisa mengerjakan "periksa dan tulis" sebagai
satu operasi yang tidak bisa disela. `RETURNING` yang kosong berarti kamu kalah balapan, dan
itu jawaban yang sama sahnya dengan menang.

**2. Konflik bukan error.** Percabangan "sudah pernah diproses" harus jalan normal, bukan
lewat `except`, dan jawabannya adalah jawaban percobaan pertama yang kamu simpan.

**3. Klaim dan pekerjaannya satu transaksi, dan commit-nya cuma sekali.** Kalau kamu menyimpan
klaimnya lebih dulu lalu commit, ada jeda di mana server boleh mati: eventnya tercatat sudah
diproses, tapi baris ledger dan saldonya tidak pernah ada — dan semua pengiriman ulang
sesudahnya akan dianggap duplikat. Dobel bisa kamu lihat. Hilang tidak.

**4. Saldo bukan soal idempotensi, tapi ketemu di lab yang sama.** Kenapa `make check` G2
merah padahal cuma 20 baris ledger yang masuk, dan kenapa `account.balance = account.balance +
nominal` di Python bukan operasi yang sama dengan `SET balance = balance + nominal` di SQL?

---

## Jebakan yang harus kamu hindari

Setelah unique key terpasang, jalan tercepat untuk membuat error di log hilang adalah:

```python
try:
    session.flush()
except IntegrityError:
    pass
```

Ini terasa benar, karena hasilnya memang "tidak ada baris ganda". Dua hal yang terjadi
sesudahnya:

**Transaksinya sudah mati.** Di Postgres, statement yang gagal membatalkan seluruh transaksi.
Statement apa pun setelah `IntegrityError` yang tidak ditangani akan gagal dengan `25P02`
("current transaction is aborted"). Kalau kamu menelan error itu dan lanjut, sisa pekerjaanmu
di request itu **tidak jalan** — dan kalau kamu mengembalikan HTTP 200, kamu baru saja bilang
"beres" untuk pekerjaan yang tidak terjadi.

**Kalau kamu menanganinya, kamu perlu `SAVEPOINT`** supaya rollback-nya terbatas sampai
statement itu saja.

Karena itu hint 3 mengarahkan kamu ke `ON CONFLICT DO NOTHING`: bukan sebagai trik supaya
error-nya hilang, tapi supaya tidak pernah ada error yang perlu ditangani. Konflik yang bisa
diprediksi bukan pengecualian.
