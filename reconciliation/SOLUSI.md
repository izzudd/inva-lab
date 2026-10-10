# Solusi — kunci yang benar bukan kunci yang unik

Untuk kamu yang sudah menyerah dan mau tahu jawabannya, atau yang ingin memverifikasi.

## Hasil pengukuran

Semua baris di bawah ini diukur dengan `scripts/check.py` yang sama, di mesin yang sama, satu
`make reset` sebelum tiap pengukuran. Pemeriksaannya 24.

| varian | merah | catatan |
|---|---|---|
| kondisi awal (branch `main`) | **14 dari 24** | kunci jalur webhook (`event_id`) dan kunci job (`recon:<run>:<charge>`) tidak pernah bertemu |
| klaim pindah ke `charge_id`, tapi job tetap punya tabel klaimnya sendiri | **13 dari 24** | yang merah beda: sekarang job-nya kena unique di ledger, jadi balasannya 500 — hujan duplicate key, lagi |
| nominal yang sudah tercatat ditimpa laporan (`F1`–`F3`) | **3 dari 24** | barisnya tetap satu, tapi nominal yang benar sudah hilang tanpa jejak |
| klaim per pembayaran di kedua jalur, dua kebijakan, tanpa kursor | **0 dari 24** | — |

Angka-angka konkret dari `make demo` di kondisi awal (hari `2026-10-09`, enam pembayaran
seharga 220.000):

- 3 webhook malam itu + job paginya → 9 baris untuk 6 pembayaran (tiga di antaranya dobel).
- webhook yang telat akhirnya sampai → 12 baris untuk 6 pembayaran; saldo 665.000 dari 220.000.
- job dijalankan dua kali: `inserted=6` di kedua run (bukan 6 lalu 0).
- dua run bersamaan: 12 baris, saldo naik 420.000 dari 210.000.
- nominal berbeda: 2 baris untuk 1 pembayaran, `mismatched=[]`.

Di branch `solusi`, `make demo` menghasilkan satu baris per pembayaran dan saldo tepat
225.000 (seed) + 220.000.

---

## Urutannya, dan kenapa urutannya penting

**1. Setiap bagian benar sendiri-sendiri. Itu masalahnya.**

Jalur webhook di kondisi awal adalah jawaban lab sebelumnya: klaimnya `event_id`, satu statement
`ON CONFLICT DO NOTHING`, jawaban pertama disimpan, klaim dan pekerjaan satu transaksi. Semua
itu tetap benar — untuk pertanyaan *"apakah pesan ini sudah pernah saya terima?"*

Jalur rekonsiliasi juga benar untuk pertanyaan yang dia jawab: *"apakah run ini sudah memproses
baris laporan ini?"* Karena id run selalu baru, jawabannya selalu "belum" — dan di situlah
bugnya. Job yang dijalankan dua kali melaporkan `inserted=6` dua kali, dengan bangga.

Yang tidak pernah ada di sistem ini: satu tempat yang bisa menjawab **"apakah pembayaran ini
sudah pernah saya catat?"** Dua jalur, dua tabel, dua kebenaran.

**2. Kuncinya pindah dari pesan ke faktanya.**

```
sebelum:  processed_events(event_id PK)     satu pesan satu klaim
sesudah:  payment_claims(charge_id PK)      satu pembayaran satu klaim
```

Praktisnya: kunci klaimnya jadi `charge_id`, dan itu kunci yang **sama** untuk kedua jalur
karena keduanya sedang membicarakan pembayaran yang sama. `event_id` tetap disimpan di ledger
dan di klaim (`first_message_id`), tapi perannya berubah: dia jejak, bukan penentu.

Ikutannya di database: unique di `ledger_entries` pindah dari `event_id` ke `charge_id`, karena
yang tidak boleh dua kali itu pembayarannya. Di produksi ini migrasi yang harus dikerjakan
hati-hati — duplikat lamanya dibereskan dulu (dan itu keputusan bisnis: baris mana yang benar),
baru constraint-nya dipasang.

**3. Dua jalur, dua kebijakan — dan itu bukan inkonsistensi.**

Waktu klaimnya sudah dipegang pihak lain, yang dilakukan kedua jalur berbeda:

| | klaim sudah ada, isinya sama | klaim sudah ada, nominal berbeda |
|---|---|---|
| **webhook** | balas jawaban pengiriman pertama (200) | **409** |
| **job rekonsiliasi** | lewati (`skipped`) | **laporkan** di `mismatched`, jangan tulis apa pun |

Alasannya beda penunggunya. Di ujung jalur webhook ada koneksi HTTP yang sedang menunggu
jawaban: dia berhak dapat jawaban yang sama, dan kalau isinya bertentangan, 409 adalah jawaban
yang benar. Di ujung jalur rekonsiliasi ada job yang sedang menyisir satu hari laporan: kalau
satu baris jelek membuat seluruh hari gagal, job-nya tidak akan pernah selesai — dan besok pagi
baris yang sama akan menggagalkannya lagi.

**4. Run yang diulang, tumpang tindih, atau kepotong selesai sendiri.**

Begitu klaimnya per pembayaran, tidak ada lagi yang perlu dicatat tentang "sudah sampai mana".
Menjalankan ulang satu hari penuh aman, dua run bersamaan aman (yang kalah klaim melewati baris
itu), dan run yang cuma sempat dua baris bisa dilanjutkan oleh run berikutnya. Itu sebabnya
pemeriksaan C, E, dan G hijau tanpa satu baris kode tambahan: **kursor itu gejala, bukan
kebutuhan.**

---

## Jebakan yang sengaja dibiarkan

**Memberi jalur kedua tabelnya sendiri.** Kelihatan paling rapi: kode jalur webhook tidak
disentuh, job punya tabelnya sendiri (`recon_claims(run_id, charge_id)`), tidak ada yang
bertabrakan. Yang terjadi sesudahnya terukur: 13 dari 24 merah, dan bentuk gagalnya berubah —
sekarang job-nya kena unique constraint di ledger, jadi balasannya HTTP 500, dan semua yang
sudah pernah dicatat lewat webhook jadi error yang harus ditangani.

**Menganggap laporan settlement sebagai kebenaran.** Varian "yang tercatat ditimpa laporan":
barisnya tetap satu, tapi nominal yang benar-benar terjadi sudah hilang tanpa jejak, dan saldo
naik 141.000 padahal seharusnya 140.000 (F1–F3 merah, 3 dari 24). Kalau kamu memutuskan laporan
memang lebih benar, keputusan itu boleh — tapi harus disengaja, dan selisihnya tetap dicatat,
bukan ditelan.

**Menggagalkan job supaya "kelihatan".** Job yang melempar error di baris pertama laporan yang
jelek akan berhenti di situ selamanya, dan laporan hari itu tidak pernah selesai.

---

## Alurnya

```
                    ┌──────────────────────────────┐
   webhook ────────►│  payment_claims              │◄──────── job rekonsiliasi
   (X-Event-Id)     │  charge_id  PRIMARY KEY      │          (laporan settlement)
                    │  request_fingerprint         │
                    │  response_status/body        │
                    └──────────────┬───────────────┘
                                   │ klaim menang?
                    ┌──────────────┴───────────────┐
                    │ ya                           │ tidak
                    ▼                              ▼
        BEGIN                              finger-print sama?
        INSERT ledger_entries (charge_id,   ├─ ya  → webhook: 200 + jawaban pertama
          event_id, source, amount)         │        job: skipped
        UPDATE accounts SET balance +=      └─ beda → webhook: 409
        COMMIT  (klaim + ledger + saldo              job: mismatched (dilaporkan,
                 satu transaksi)                            tidak ditulis)
```

Yang harus dijaga:

1. Kunci klaim = **fakta** (`charge_id`), bukan pesan. Kalau ada jalur ketiga besok, dia
   memakai kunci yang sama.
2. Klaim, ledger, dan saldo **satu transaksi**, satu `COMMIT`.
3. Kebijakan waktu konflik **per jalur**, dan alasannya adalah siapa yang menunggu di ujung.
4. Tidak ada kursor, tidak ada id run di kunci, tidak ada tabel progres.

## Pertanyaan buat kamu

1. Job ini jalan tiap pagi untuk hari kemarin. Kalau gateway-nya baru mengirim laporan hari itu
   tiga hari kemudian, apa yang harus berubah — kode job-nya, atau jadwalnya?
2. Kalau sebuah charge bisa punya dua fakta berbeda (refund setelah pembayaran), kunci apa yang
   benar, dan kenapa `charge_id` sendirian tidak cukup?
3. Webhook membalas 409 untuk nominal yang bertentangan, job melaporkannya. Apa yang lebih baik
   untuk pengguna akun: baris penyesuaian otomatis, atau laporan harian yang harus dilihat
   manusia? Siapa yang harus memutuskan?
4. Kalau `reconciliation_runs` dihapus sama sekali, apa yang hilang dari sistem ini? (Jawab
   dulu sebelum menghapusnya.)
