# Lab 2 — Satu pembayaran, empat baris di ledger

Bagian dari repo [`inva-lab`](../README.md). Semua perintah di bawah ini dijalankan dari
direktori `idempotency/`.

```bash
make up      # nyalain db + API
make replay  # putar ulang satu event, seperti yang dilakukan gateway
make check   # target lab ini
```

`POST /webhooks/payments` menerima notifikasi pembayaran dari gateway. Di laptop, dengan tiga
akun dan dua event, endpoint ini jalan mulus: satu request masuk, satu baris ledger keluar,
saldo naik. Nggak ada yang kelihatan salah — dan memang, kodenya nggak salah.

Yang nggak kelihatan: **HTTP nggak punya cara memberi tahu pengirim bahwa jawaban kita
sampai.** Gateway mengirim event, kita commit transaksinya, lalu jawabannya hilang di jalan —
koneksi putus, load balancer timeout, container kita di-restart sedetik terlalu cepat. Dari
sisi kita semuanya beres. Dari sisi gateway, eventnya belum pernah diterima, jadi dia kirim
lagi. Besoknya lagi.

Itu bukan gateway yang rusak. Itu satu-satunya pilihan yang dia punya, dan dia memilih **dobel
daripada hilang** — karena kehilangan pembayaran lebih mahal daripada mengulangnya. Dobelnya
jadi pekerjaanmu.

Ini yang terjadi di lab ini:

| | sekarang |
|---|---|
| satu event dikirim ulang 4× | **4 baris** ledger untuk 1 event, saldo naik **4× nominal** |
| satu event dikirim 30× sekaligus | **30 baris**, dan saldo cuma naik sebagian (di mesin penulis lab: 40.000–60.000 dari 300.000 yang seharusnya) |
| 3 event berbeda, masing-masing dikirim 2× | **6 baris**, saldo naik **6× nominal** |
| request yang persis sama dikirim 2× | **2 baris** — nggak ada apa pun di database yang bisa membedakan mana yang sudah pernah diproses |

## Misi kamu

Bikin `make check` hijau. Empat syarat:

1. **Tepat sekali.** Satu event diterapkan tepat satu kali. Tidak dobel, dan tidak ada yang
   hilang: tiga event berbeda tetap jadi tiga baris ledger, bukan enam, bukan dua.
2. **Pengiriman ulang dijawab seperti jawaban pertama.** Bukan error, bukan pesan "sudah
   diproses" — body yang sama, dengan `entry_id` yang sama. Ini berlaku juga saat pengiriman
   ulangnya datang bersamaan. Alasannya bukan sekadar sopan: jawaban yang dihitung ulang dari
   keadaan database **saat itu** bisa salah, karena saldonya sudah berubah oleh event lain.
   Yang benar adalah jawaban dari percobaan pertama, apa adanya.
3. **`event_id` yang dipakai ulang dengan isi berbeda tidak ikut diproses.** Nominal yang
   berbeda untuk event yang sama tidak boleh masuk ke ledger.
4. **Saldo tetap benar saat banyak event datang bersamaan.** Tiga puluh event *berbeda* yang
   datang sekaligus harus menaikkan saldo tiga puluh kali nominal, bukan dua kali. Ini datang
   dari komplain kedua, bukan dari yang pertama: ada merchant yang saldonya lebih kecil dari
   yang seharusnya, dan gateway-nya tidak salah.

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
tempat yang salah. Yang pertama kelihatan setelah kamu memperbaiki bugnya, bukan sebelum —
dan di situlah muncul "duplicate key value violates unique constraint" yang mungkin sudah
tidak asing buatmu.

Kode awalnya kelihatan sudah benar, dan itu disengaja. Ada bagian di dalamnya yang ditulis
dengan niat baik, lengkap dengan komentar yang menjelaskan kenapa bagian itu ada. Baca
komentarnya pelan-pelan: itu satu-satunya penjagaan yang dimiliki endpoint ini, dan itu
penjagaan yang salah tempat.

## Batas lab ini

Dua hal yang **tidak** ada di sini, dan sengaja: keduanya lebih sulit daripada yang ada.

- **Efek samping ke luar database.** Kalau handler-mu juga mengirim email atau memanggil API
  pihak ketiga, "taruh di satu transaksi" nggak menolong: email nggak bisa di-rollback. Itu
  pola outbox, dan itu bukan lab ini.
- **Fakta yang datang dari dua jalur.** Di sini satu pembayaran cuma punya satu jalur: webhook
  gateway. Begitu ada job rekonsiliasi yang menutup pembayaran yang webhook-nya telat, semua
  kunci yang kamu pakai di lab ini berhenti bekerja — dan yang bekerja tinggal kunci yang
  berasal dari domainnya sendiri (nomor referensi pembayaran), bukan dari transportnya. Itu
  lab berikutnya.
