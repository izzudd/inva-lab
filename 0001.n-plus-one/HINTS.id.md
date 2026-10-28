# Hints

Buka satu per satu. Tiap hint cuma kasih pertanyaan berikutnya, bukan jawabannya.

---

## Hint 1 — dari mana 41 query itu

Empat puluh satu query. Kelompokkan dulu angkanya sebelum mengubah apa pun.

Ada tiga kelompok. Satu untuk daftar post. Dua kelompok lagi, masing-masing muncul sekali
per post yang kamu proses — dan itu berarti keduanya ada di dalam perulangan.

Setelah ketemu, jangan benerin dua-duanya sekaligus. Jawab dulu: **dari dua kelompok itu,
mana yang sebenarnya bikin lambat?** Salah satu kelompok jauh lebih mahal dari yang lain.
Kalau kamu salah menebak, kamu bakal benerin yang murah, melihat hasilnya hampir nggak
berubah, dan bingung.

Petunjuk untuk memutuskan: bandingkan kolom apa yang dipakai untuk mencari di masing-masing
kelompok. Satu kelompok mencari berdasarkan kunci utama — itu pencarian paling murah yang
bisa dilakukan database. Kelompok yang lain mencari berdasarkan kolom biasa.

---

## Hint 2 — query-nya sudah 2, kok masih merah

Selamat, query kamu tinggal 2. Sekarang lihat baris kedua `make check`: masih sekitar
60 ms, dan targetnya 30 ms.

Query-nya sedikit. Berarti masalahnya bukan jumlahnya.

Jawab ini di luar aplikasi:

```bash
make psql
```

```sql
EXPLAIN ANALYZE SELECT count(*) FROM comments WHERE post_id = 7;
```

Perhatikan dua hal: jenis scan-nya apa, dan berapa baris yang dibaca untuk menghasilkan
satu angka.

750.000 baris dibaca untuk menjawab satu pertanyaan sederhana "ada berapa komentar di post
ini". Pertanyaan berikutnya: kenapa Postgres membaca sejauh itu, padahal kamu hanya minta
satu angka?

---

## Hint 3 — dua perbaikan, di dua tempat berbeda

Ada **dua** hal yang harus berubah, dan keduanya bukan di file yang sama.

**1. Di aplikasi.** Query yang terakhir tersisa, yang menghitung komentar, dijalankan
sekali per post. Padahal kamu nggak butuh barisnya sama sekali — kamu cuma butuh angkanya.
Kumpulkan semua id post dalam satu halaman, lalu ambil seluruh angkanya dalam **satu** query
yang dikelompokkan (`GROUP BY`).

Sampai sini: 2 query, tapi `make check` masih merah di baris latency.

**2. Di database.** `comments.post_id` nggak punya index. Ini bagian yang paling sering
diabaikan, karena "kodenya sudah benar" — dan memang benar, yang salah datanya.

Di produksi, tabel `comments` nggak akan kosong, jadi index harus dibuat tanpa mengunci
tabel:

```sql
CREATE INDEX CONCURRENTLY idx_comments_post_id ON comments (post_id);
```

Kenapa `CONCURRENTLY` penting, dan apa harganya — itu pertanyaan untuk lab berikutnya.

---

## Jebakan yang harus kamu hindari

Cara paling cepat membuat query jadi 2 adalah memangggil relasi komentarnya sekaligus, lalu
memakai `len()` di atasnya. Ini terasa seperti jawaban yang benar, karena *eager loading*
memang solusi yang ditulis di hampir semua artikel tentang N+1.

Query-nya langsung jadi 2. Tapi perhatikan `make check`: **masih ~1.000 ms.**

Yang terjadi: 20 post × ~1.875 komentar = **37.500 baris** dipindahkan dari database ke
memori aplikasi, cuma supaya Python bisa menghitungnya dengan `len()`. Database berhenti
bekerja keras; sekarang aplikasi yang bekerja keras. Tambahkan index pun nggak menolongnya —
data itu tetap harus menyeberang.

Menghitung nggak butuh datanya. Butuh angkanya.
