# Hints

Buka satu per satu. Tiap hint cuma kasih pertanyaan berikutnya, bukan jawabannya.

---

## Hint 1 — dua baris untuk satu pembayaran, dan dua-duanya merasa benar

Jalankan `make demo`. Perhatikan kolom `source` di setiap baris: satu baris datang dari
`webhook`, satu lagi dari `recon`. Pembayarannya sama — `charge_id`-nya sama — tapi yang
membedakannya di kedua jalur itu bukan pembayarannya.

Tiga pertanyaan:

1. Jalur webhook memakai kunci apa untuk memutuskan "ini sudah pernah aku catat"? Jalur
   rekonsiliasi memakai kunci apa? Buka `api/app/ledger.py` dan bandingkan dua fungsi di
   dalamnya.
2. Dari dua kunci itu, yang mana yang berasal dari **pembayarannya**, dan yang mana yang
   berasal dari **pesan yang memberitahukannya**?
3. Kunci yang berasal dari pesan itu sifatnya apa kalau ada jalur kedua? Dan kenapa jalur
   rekonsiliasi harus membuat kuncinya sendiri, bukan memakai kunci dari jalur webhook?

---

## Hint 2 — job-nya sendiri juga belum aman dijalankan lagi

Jalankan `make check`, lalu lihat pemeriksaan C. Job dijalankan lagi untuk hari yang sama, dan
dia melaporkan `inserted=6` — bukan `0`.

Pertanyaan:

1. Lihat kunci klaim yang dibuat `record_from_settlement` di `ledger.py`. Bagian mana dari kunci
   itu yang berubah tiap kali job dijalankan? Dan kenapa penulisnya menaruh bagian itu di sana
   (petunjuk: lihat komentarnya, dan lihat baris mana di `ledger_entries` yang diisi dari situ)?
2. Kalau kuncinya tidak lagi memuat id run, apa lagi yang dibutuhkan job ini supaya dua run
   yang tumpang tindih tidak saling menimpa? *(Jawaban "tidak ada" itu sah — coba buktikan
   kenapa.)*
3. Lihat `mismatched` di ringkasan job: selalu `[]`, padahal pemeriksaan F menyiapkan laporan
   yang nominalnya beda. Informasi itu ada di mana? Siapa yang seharusnya membandingkan?

---

## Hint 3 — empat keputusan

Semuanya satu tema: **kunci yang benar adalah kunci milik faktanya, dan kebijakan waktu
menemukan keanehan berbeda per jalur.**

**1. Klaimnya jadi klaim tentang pembayaran, bukan tentang pesan.** Ganti tabel `processed_events`
menjadi klaim ber-`charge_id` sebagai primary key: `payment_claims(charge_id, ...)`. Kunci ini
sama untuk jalur webhook dan jalur rekonsiliasi, karena keduanya sedang membicarakan pembayaran
yang sama. `event_id` tetap disimpan, tapi sebagai jejak pesan pertama yang memberitahukannya —
bukan sebagai penentu.

**2. Unique di ledger-nya ikut pindah.** `ledger_entries.event_id` yang unik tidak lagi berarti
apa-apa begitu kuncinya pindah; yang harus unik adalah `charge_id`. Di database produksi, ini
migrasi yang harus dikerjakan hati-hati: duplikat yang sudah ada harus dibereskan dulu.

**3. Dua jalur, dua kebijakan waktu klaimnya sudah ada.**
- **Webhook** (lab sebelumnya): balas dengan jawaban pengiriman pertama yang tersimpan. Yang
  isinya beda → 409, karena pengirimnya masih menunggu jawaban.
- **Job rekonsiliasi**: jangan pernah menggagalkan seluruh run cuma karena satu baris. Yang
  sudah ada dan cocok → lewati diam-diam. Yang sudah ada tapi nominalnya beda → **laporkan** di
  `mismatched` (misalnya daftar `charge_id`-nya), jangan ditimpa, jangan ditambah baris.
  Job yang satu baris jeleknya bikin seluruh hari gagal itu job yang tidak akan pernah selesai.

**4. Setelah dua itu beres, run yang tumpang tindih dan run yang kepotong selesai sendiri.**
Tidak perlu kursor, tidak perlu tabel progres, tidak perlu id run di kunci: menjalankan ulang
satu hari penuh aman, karena tiap pembayarannya mengklaim dirinya sendiri. Itu sebabnya
pemeriksaan E dan G hijau tanpa kamu menulis satu baris pun untuk mereka.

---

## Jebakan yang harus kamu hindari

**Memberi jalur kedua tabelnya sendiri.** Ini yang paling menggoda: biarkan klaim webhook apa
adanya, dan bikin tabel klaim untuk job. Hasilnya sama seperti sekarang — dua jalur, dua tabel,
dua kebenaran. Yang harus disatukan adalah **kuncinya**, bukan alatnya.

**Mempercayai laporan settlement sebagai kebenaran.** Laporan itu juga cuma klaim: nominalnya
bisa beda dengan yang sudah kita catat, dan baris bisa muncul dua kali kalau gateway mengirim
ulang laporannya. Job yang menulis apa pun yang dilihatnya akan menulis tiga kali untuk satu
pembayaran pada hari ketiga.

**Membalas error supaya job-nya "berhenti dan kelihatan".** Job yang mati di baris pertama
laporan yang jelek akan berhenti di situ selamanya. Baris yang tidak cocok dilaporkan, bukan
dijadikan alasan untuk berhenti.
