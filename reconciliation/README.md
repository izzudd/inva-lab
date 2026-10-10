# Lab 3 — Satu pembayaran, tiga jalur

Bagian dari repo [`inva-lab`](../README.md). Semua perintah di bawah ini dijalankan dari
direktori `reconciliation/`.

```bash
make up      # nyalain db + API + gateway (tiruan)
make demo    # cerita lengkapnya: webhook malam itu, job paginya, webhook yang telat
make check   # target lab ini
```

Sistemnya sudah lewat lab sebelumnya: jalur webhook-nya sudah idempotent. Yang baru adalah
**jalur kedua**. Kalau ada pembayaran yang webhook-nya tidak pernah sampai — gateway-nya down,
kita yang down, atau koneksinya putus di tengah — ada job pagi yang membaca **laporan
settlement** dari gateway dan menutup yang belum tercatat.

Dua jalur untuk satu fakta yang sama. Dan tidak ada satu pun dari jalur itu yang tahu bahwa
jalur satunya ada.

Ini yang terjadi di lab ini (angka dari `make demo`, satu hari di mana gateway sempat down):

| | sekarang |
|---|---|
| 3 webhook malam itu, lalu job rekonsiliasi paginya | 6 pembayaran jadi **9 baris** — 3 di antaranya punya dua baris, satu dari tiap jalur |
| webhook yang telat akhirnya sampai | 6 pembayaran jadi **12 baris** — semuanya dobel, saldo 665.000 dari 220.000 yang seharusnya |
| job rekonsiliasi dijalankan dua kali | **6 baris baru** tiap kali dijalankan, dan job-nya melaporkan `inserted=6` (bukan 0) |
| dua run job jalan bersamaan | **12 baris** untuk 6 pembayaran, saldo naik 420.000 dari 210.000 |
| laporan settlement beda nominal dengan yang sudah tercatat | **2 baris** untuk 1 pembayaran, dan `mismatched` tetap kosong |

## Misi kamu

Bikin `make check` hijau. Tiga syarat:

1. **Satu pembayaran, satu baris.** Dari jalur mana pun, dan berapa kali pun jalurnya
   dipanggil. Enam pembayaran di laporan = enam baris ledger, bukan sembilan, bukan dua belas.
2. **Job boleh dijalankan lagi, dan laporannya jujur.** Run kedua untuk hari yang sama tidak
   menambah baris dan melaporkan `inserted=0`. Run yang cuma sanggup memproses sebagian
   (`limit=2`) boleh dilanjutkan kapan saja tanpa mendobel. Dua run yang tumpang tindih juga
   tidak boleh mendobel.
3. **Nominal yang sudah tercatat tidak berubah diam-diam.** Kalau laporan settlement menyebut
   nominal yang berbeda dengan yang sudah ada di ledger, barisnya tetap satu, nominalnya tetap
   yang pertama, dan perbedaannya **dilaporkan** di ringkasan job (`mismatched`).

Boleh mengubah apa saja, kecuali:

- kontrak `GET /api/accounts/:id`, `GET /api/accounts/:id/entries`, `POST /jobs/reconcile`
  (balasannya dipakai `make check`), dan gateway tiruannya (`gateway/`)
- isi `db/init/02_seed.sql`

## Di mana mulainya

```bash
make demo        # jalankan ini dulu: ceritanya, bukan angkanya
make settlement  # laporan settlement yang dibaca job
make entries     # baris ledger akun 1 (di dalamnya ada kolom `source`)
make jobs        # riwayat run rekonsiliasi
make psql        # masuk ke database
```

Gateway-nya tiruan dan laporannya dibangkitkan dari tanggalnya, jadi tanggal yang sama selalu
menghasilkan pembayaran yang sama. Kamu bisa pakai tanggal apa pun: `make demo DAY=2024-03-17`.

## Sebelum buka jawabannya

Kalau macet, buka `HINTS.md` sesuai urutan. Jangan lompat ke hint 3.

- nyangkut 45 menit → hint 1
- nyangkut 90 menit → hint 2
- menyerah → hint 3, dan **tulis di mana kamu nyerah**

Jangan buka branch `solusi` sebelum kamu benar-benar mentok.

## Kenapa ini ada

Di lab sebelumnya, "pembayaran" dan "pesan yang memberitahukan pembayaran itu" kebetulan
selalu datang berpasangan, jadi tidak pernah ada bedanya. Begitu ada jalur kedua, bedanya jadi
yang paling penting di seluruh sistem: **kunci yang benar bukan kunci yang unik, tapi kunci
yang dimiliki oleh faktanya, bukan oleh pesannya.**

Dan bagian kedua yang lebih halus: dua jalur yang sama-sama benar bisa butuh **kebijakan yang
berbeda** waktu menemukan keanehan. Webhook boleh membalas 409 untuk satu event yang aneh;
job rekonsiliasi tidak boleh mati cuma karena satu baris laporan tidak cocok.

## Batas lab ini

- **Satu charge = satu fakta.** Di sini satu pembayaran cuma punya satu kemungkinan isi. Begitu
  ada event kedua tentang charge yang sama yang memang fakta baru — refund, chargeback,
  pembayaran sebagian — kunci `charge_id` sendirian tidak cukup lagi: kamu butuh kunci per
  (charge, jenis fakta), dan aturan tentang urutan kejadiannya.
- **Siapa yang menang itu keputusan bisnis.** Di lab ini aturannya "yang tercatat dulu yang
  menang, selisihnya dilaporkan". Ada sistem yang memilih sebaliknya (settlement terakhir yang
  menang, dengan baris penyesuaian). Yang tidak boleh: memilih tanpa sadar.
