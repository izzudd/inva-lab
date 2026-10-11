# Solusi — dan kenapa unique key sendirian nggak cukup

Untuk kamu yang sudah menyerah dan mau tahu jawabannya, atau yang ingin memverifikasi.

## Hasil pengukuran

Semua baris di bawah ini diukur dengan `scripts/check.py` yang sama, di mesin yang sama, satu
`make reset` sebelum tiap pengukuran. Pemeriksaannya 21; yang dihitung di sini berapa di
antaranya merah.

| varian | merah | yang masih merah |
|---|---|---|
| kondisi awal (branch `main`) | **11 dari 21** | B1, B2, D1a–D3a, E1, E2, C2, F1, F2, G2 |
| (1) + `UNIQUE (event_id)` di database, handler tidak diubah | **7 dari 21** | C1, C2, D1b–D3b, F3, G2 |
| (2) + klaim `ON CONFLICT DO NOTHING`, tapi konflik dijawab pesan | **1 dari 21** | C2 |
| (3) + jawaban pengiriman pertama disimpan di baris klaimnya | **1 dari 21** | G2 |
| (4) + saldo dihitung database, bukan dibaca-ubah-tulis di Python | **0 dari 21** | — |
| alternatif untuk (2): periksa dulu di aplikasi, baru `INSERT` | **3 dari 21** | D1b–D3b |

Angka yang berubah-ubah tergantung balapan di mesinmu (semuanya dari tabel di atas):

- `C1` di varian 1: `status: [200, 500, 500, 500]` — ini "duplicate key" yang muncul di log.
- `D1b`–`D3b` di varian 1: 1 dari 30 pengiriman dijawab 2xx, 29 sisanya 500.
- `G2` di varian 1–3: saldo naik 30.000–40.000 dari 300.000 yang seharusnya.
- `D1b`–`D3b` di varian alternatif: 26–29 dari 30 pengiriman dijawab 500, nggak pernah 30.

---

## Urutannya, dan kenapa urutannya penting

**1. Yang salah bukan kodenya. Yang salah asumsinya.**

`handlers.py` di kondisi awal tidak punya penjagaan apa pun, dan komentarnya menjelaskan kenapa
penulisnya merasa itu cukup: *"endpoint ini membalas 200 setelah transaksinya commit, jadi satu
event sampai ke sini tepat satu kali."*

Dua kejadian di situ dianggap satu. Kenyataannya `session.commit()` dan jawaban 200 yang sampai
ke gateway adalah **dua kejadian terpisah**, dan yang kedua bisa gagal sendirian. Kalau gagal,
gateway cuma tahu satu hal: dia belum menerima balasan. Jadi dia mengirim lagi — dan dia benar
untuk melakukannya, karena pilihan satunya adalah menganggap pembayaran yang gagal di tengah
sebagai "selesai".

Ini lapis pertama, dan yang paling sering kejadian sungguhan: **bukan bug, tapi asumsi tentang
transport yang nggak pernah ditulis, dan nggak pernah diuji.** Nggak ada error, nggak ada
warning, cuma baris yang bertambah.

**2. Unique key memperbaiki gejalanya, lalu memunculkan masalah baru — dan masalah baru itu benar.**

Tambahkan `UNIQUE (event_id)`. Dobelnya berhenti (D1a–D3a langsung hijau). Yang muncul:

```
C1 status: [200, 500, 500, 500]
D1b 1 dari 30 pengiriman dijawab 2xx
sqlalchemy.exc.IntegrityError: (psycopg2.errors.UniqueViolation)
duplicate key value violates unique constraint "ledger_entries_event_id_key"
```

Ini yang bikin orang mengira unique key itu "bukan solusi". Padahal constraint-nya benar dan
database-nya benar. Yang salah adalah **reaksi kita terhadap konflik itu**: kita
memperlakukannya sebagai kegagalan, padahal dari sudut pandang gateway, "event ini sudah pernah
saya kirim dan sudah pernah diterima" adalah hasil yang sukses.

Perhatikan juga apa yang **tidak** rusak: saat itu barisnya tetap satu dan saldonya tetap
benar. Jadi duplicate key bukan masalah data — dia masalah **jawaban**. Gateway nggak pernah
tahu percobaan pertamanya berhasil, jadi dia mengirim ulang, dapat 500 lagi, mengirim ulang
lagi. Yang bertambah bukan barisnya, tapi error-nya.

**3. Keputusannya pindah ke database, dan jawabannya disimpan.**

Dua perubahan, dan dua-duanya soal tempat menyimpan:

- `processed_events.event_id` sebagai primary key. Satu statement:

  ```sql
  INSERT INTO processed_events (event_id, request_fingerprint)
  VALUES ($1, $2)
  ON CONFLICT (event_id) DO NOTHING
  RETURNING event_id;
  ```

  Kosong = bukan kita yang dapat. Ini "periksa dan tulis" dalam satu operasi, jadi nggak ada
  jendela waktu yang bisa dilewati dua-duanya. Nggak ada `except` yang perlu ditulis, karena
  konflik yang bisa diprediksi bukan pengecualian.

- Jawaban pengiriman pertama disimpan di baris itu, dan pengiriman ulang mengembalikannya.
  Kalau kamu cuma menjawab `{"status":"ignored"}`, nggak ada yang dobel — tapi gateway tetap
  nggak tahu apa yang terjadi, dan `make check` C2 tetap merah.

**3b. Kalau kamu memilih "periksa dulu di aplikasi, baru `INSERT`", kenapa masih merah.**

Bentuk ini kelihatan setara, dan di tes manual dia memang hijau. Yang terjadi di bawah beban: 30
pengiriman membaca tabelnya bersamaan, semuanya melihat "belum ada", semuanya menulis. 26–29 di
antaranya ditangkap unique key dan jadi 500 (D1b–D3b). Hasil akhirnya nggak dobel, tapi
endpoint-mu berteriak di hampir semua pengiriman yang bersamaan — dan itu justru masalah yang
mau dihapus lab ini.

**4. Saldo bukan soal idempotensi. Tapi ketemu di lab yang sama.**

`account.balance = account.balance + nominal` kelihatan seperti penjumlahan. Yang sebenarnya
terjadi: baca nilai dari database, kirim balik nilai barunya. Tiga puluh transaksi yang membaca
nilai yang sama akan menulis nilai yang sama — 40.000 dari 300.000 yang terselamatkan (G2).
Di SQL, satu statement `UPDATE accounts SET balance = balance + $1 WHERE id = $2` nggak punya
masalah itu: database yang memegang barisnya selama update.

Pelajaran yang sama dengan tiga langkah sebelumnya, dalam bentuk yang paling murni: **kalau
datanya ada di database, keputusannya di database juga.**

---

## Jebakan yang sengaja dibiarkan

**Menelan `IntegrityError` dan lanjut.** Ini yang paling menggoda setelah unique key muncul:

```python
try:
    session.flush()
except IntegrityError:
    pass
```

Terlihat aman karena baris gandanya memang nggak jadi masuk. Yang nggak kelihatan: di Postgres,
statement yang gagal membatalkan **seluruh transaksi**. Statement berikutnya di transaksi itu
gagal dengan `25P02: current transaction is aborted, commands ignored until end of transaction
block`, dan kalau kamu menangkap error itu juga lalu mengembalikan HTTP 200, kamu baru saja
bilang "beres" untuk pekerjaan yang nggak terjadi. Kalau kamu tetap mau menangani
pengecualian, kamu butuh `SAVEPOINT` supaya yang dibatalkan cuma statement itu.

**Memisahkan klaim dari pekerjaannya.** Kalau kamu commit klaimnya lebih dulu, baru mengerjakan
ledger dan saldo, ada satu jendela waktu di mana server boleh mati. Sesudah itu: eventnya
tercatat sudah diproses, ledger dan saldo kosong, dan semua pengiriman ulang sesudahnya
dianggap duplikat. Dobel kelihatan di laporan. **Hilang nggak kelihatan.** Karena itu klaim,
baris ledger, dan saldo harus commit bersama — satu transaksi.

---

## Alurnya

```
POST /webhooks/payments
  X-Event-Id: evt_9d7c  (stabil)     X-Delivery-Id: dlv_1a2b  (baru tiap kiriman)
        │
        ▼
  ┌─────────────────────────────────────────────────────────────┐
  │ BEGIN                                                       │
  │                                                             │
  │ INSERT INTO processed_events (event_id, fingerprint)        │
  │   ON CONFLICT (event_id) DO NOTHING                         │
  │   RETURNING event_id;                                       │
  │                                                             │
  │   baris kembali?                                            │
  │   ├─ ya  → kita yang dapat event ini                        │
  │   │        INSERT ledger_entries (event_id, ...)            │
  │   │        UPDATE accounts SET balance = balance + $nominal │
  │   │        UPDATE processed_events SET response_* = jawaban │
  │   │        COMMIT  →  200 + jawaban                         │
  │   │                                                         │
  │   └─ tidak → event ini sudah milik orang lain               │
  │            ROLLBACK                                         │
  │            SELECT response_* FROM processed_events          │
  │              WHERE event_id = $1;                           │
  │                                                             │
  │            fingerprint sama?   → 200 + jawaban yang sama    │
  │            fingerprint beda?   → 409 isi berbeda            │
  │                                                             │
  └─────────────────────────────────────────────────────────────┘
```

Yang harus dijaga kalau kamu mengubahnya:

1. Klaim, pekerjaan, dan jawabannya **satu transaksi**. Satu `COMMIT`.
2. Konflik **bukan** jalur pengecualian. Nggak ada `except` di alur ini.
3. Keputusan "sudah pernah atau belum" ada **di database**, dalam satu statement.
4. Semua angka yang berubah (**saldo**) dihitung database, bukan di Python.

Catatan: `X-Delivery-Id` tetap disimpan di baris ledger, tapi cuma sebagai jejak ("pengiriman
ini datang berapa kali"). Dia **bukan** penentu apa pun. Jangan bangun keputusan di atas id
transport — begitu pembayaran yang sama bisa datang dari jalur lain, id transport nggak bisa
menolongmu lagi.

## Kalau kamu percaya klaim di halaman ini

Satu-satunya klaim di sini yang nggak bisa kamu buktikan dari `make check` adalah perilaku
`ON CONFLICT DO NOTHING` waktu barisnya masih dipegang transaksi lain: apakah dia **menunggu**,
dan kalau yang dipegang ternyata batal, apakah penyisipnya jadi menyisipkan? Itu penting,
karena kalau jawabannya "tidak menunggu", klaim event bisa hilang.

```bash
make probe
```

Hasilnya di mesin penulis lab:

```
A: menyisipkan 'x', belum commit
B: selesai dalam 1,5 detik? belum - B sedang menunggu
A: rollback
B: selesai setelah 1.50 detik, baris yang dimasukkan = 1
isi tabel setelah semuanya selesai: 1 baris
```

Dia menunggu, dan kalau yang dipegang batal, penyisipnya tetap menyisipkan. Karena itu di
`handlers.py` ada satu cabang `503` yang nggak pernah muncul di lab ini: kalau suatu saat kamu
menemukan jalur di mana klaim "tidak dapat" tapi barisnya juga "tidak ada", jawabannya adalah
"coba lagi", bukan "sudah beres".

## Pertanyaan buat kamu

1. Kenapa `ON CONFLICT DO NOTHING` lebih aman daripada `SELECT` lalu `INSERT`, padahal keduanya
   sama-sama memeriksa `event_id`?
2. Kalau tabel `ledger_entries` sudah punya 4 juta baris dan 8.000 di antaranya duplikat dari
   bug ini, apa urutan langkah yang benar untuk memasang unique key-nya di produksi — dan siapa
   yang memutuskan baris mana yang dibuang?
3. `request_fingerprint` di lab ini cuma `account_id:nominal`. Apa yang boleh dan nggak boleh
   kamu masukkan ke situ, kalau isi payload boleh berubah tanpa mengubah arti eventnya?
4. Kenapa jawaban pengiriman pertama harus disimpan, bukan dijawab ulang dari keadaan database
   saat itu? Coba pikirkan kasus di mana saldonya sudah berubah karena event lain.
5. Semua yang kamu kerjakan di lab ini bergantung pada satu asumsi: **satu pembayaran cuma
   punya satu jalur**. Kalau besok ada job rekonsiliasi yang menutup pembayaran yang webhook-nya
   telat — dan dia punya id sendiri, bukan `evt_...` dari gateway — bagian mana dari solusimu
   yang masih bekerja, dan bagian mana yang harus dibongkar?
