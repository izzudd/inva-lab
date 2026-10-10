# Lab 2 — Satu pembayaran, dua baris di ledger

Bagian dari repo [`inva-lab`](../README.md). Semua perintah di bawah ini dijalankan dari
direktori `idempotency/`.

```bash
make up      # nyalain db + API
make replay  # putar ulang satu event, seperti yang dilakukan gateway
make check   # target lab ini
```

`POST /webhooks/payments` menerima notifikasi pembayaran dari gateway. Di laptop, dengan
tiga akun dan dua event, endpoint ini jalan mulus dan tidak ada yang kelihatan salah. Kodenya
bahkan sudah punya penjagaan untuk "event yang datang dua kali".

Yang tidak kelihatan: **gateway mengirim ulang event yang sama setiap kali jawaban dari kita
tidak sampai.** Bukan karena mereka jahat — mereka tidak pernah tahu apakah requestnya
sampai atau tidak, jadi satu-satunya cara mereka yakin adalah mengirim lagi. Di produksi kamu
mendapat satu pengiriman, atau tiga, atau dua puluh.

Ini yang terjadi di lab ini:

| | sekarang |
|---|---|
| satu event dikirim ulang 4× (id pengiriman berbeda) | **4 baris** ledger untuk 1 event, saldo naik **4× nominal** |
| satu event dikirim 20× sekaligus | **20 baris**, dan saldo cuma naik sebagian (di mesin penulis lab: 20.000 dari 200.000 yang seharusnya) |
| request yang persis sama dikirim 2× | **1 baris**, dijawab `{"status":"ignored"}` — ini kenapa kelihatan sudah aman |
| 3 event berbeda, masing-masing dikirim 2× | **6 baris**, saldo naik **6× nominal** |

Perhatikan baris ketiga. Kalau kamu menguji endpoint ini dengan cara yang paling wajar —
kirim request yang sama dua kali — hasilnya benar. Yang salah cuma satu hal: **yang kamu
anggap "request yang sama" bukan yang dianggap "event yang sama" oleh gateway.**

## Misi kamu

Bikin `make check` hijau. Empat syarat:

1. **Tepat sekali.** Satu event diterapkan tepat satu kali. Tidak dobel, dan tidak ada yang
   hilang: tiga event berbeda tetap jadi tiga baris.
2. **Pengiriman ulang dijawab seperti jawaban pertama.** Bukan error, bukan pesan
   "sudah diproses" — body yang sama persis, dengan `entry_id` yang sama. Gateway yang
   mengirim ulang tidak tahu apa yang terjadi pada percobaan pertamanya; kalau kita
   menjawabnya dengan sesuatu yang lain, dia tetap tidak tahu. Ini berlaku juga saat
   pengiriman ulangnya datang bersamaan.
3. **`event_id` yang dipakai ulang dengan isi berbeda tidak ikut diproses.** Nominal yang
   berbeda untuk event yang sama tidak boleh masuk ke ledger.
4. **Saldo tetap benar saat banyak event datang bersamaan.** Dua puluh event *berbeda* yang
   datang sekaligus harus menaikkan saldo dua puluh kali nominal, bukan dua kali.

Boleh mengubah apa saja, kecuali:

- bentuk response `GET /api/accounts/:id` dan `GET /api/accounts/:id/entries` — itu alat
  ukurmu, dan `make check` membacanya
- isi `db/init/02_seed.sql`

## Di mana mulainya

```bash
make replay    # 4 pengiriman untuk satu event, lalu dua angka di bawahnya
make entries   # saldo + seluruh baris ledger akun 3
make psql      # masuk ke database
make logs      # log API, kalau ada yang membalas error
```

`make replay` sengaja menampilkan `X-Event-Id` dan `X-Delivery-Id` yang dikirim gateway.
Baca dua-duanya sebelum mengubah kode.

## Sebelum buka jawabannya

Kalau macet, buka `HINTS.md` sesuai urutan. Jangan lompat ke hint 3.

- nyangkut 45 menit → hint 1
- nyangkut 90 menit → hint 2
- menyerah → hint 3, dan **tulis di mana kamu nyerah** — itu bagian dari lab ini, bukan
  kegagalan

Jangan buka branch `solusi` sebelum kamu benar-benar mentok.

## Kenapa ini ada

Idempotensi bukan soal "menambah pengecekan". Ini soal memutuskan **siapa yang berhak
memutuskan** apakah sesuatu sudah pernah terjadi: aplikasimu, atau database.

Di lab ini ada dua bug dan satu jebakan, dan ketiganya ada karena keputusan itu diambil di
tempat yang salah. Yang pertama kelihatan kalau kamu membandingkan dua id di atas. Yang
kedua kelihatan setelah kamu memperbaiki yang pertama — dan di situlah muncul "duplicate key
value violates unique constraint" yang mungkin sudah tidak asing buatmu.

Kode awalnya kelihatan sudah benar, dan itu disengaja. Ada bagian di dalamnya yang ditulis
dengan niat baik, lengkap dengan komentar yang menjelaskan kenapa bagian itu ada.
