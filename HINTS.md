# Hints

Buka satu per satu. Tiap hint cuma kasih pertanyaan berikutnya, bukan jawabannya.

---

## Hint 1 — soal jumlah query, bukan soal kecepatan

91 query. Dari mana saja angkanya?

Tiga kelompok. Satu untuk daftar post. Dua kelompok lagi masing-masing muncul per post yang
kamu proses. Temukan dua baris di `api/app/repositories.py` yang menghasilkan query di dalam
perulangan.

Setelah menemukan keduanya, jawab dulu: **dari dua kelompok itu, mana yang sebenarnya bikin
lambat?** Jangan asal benerin dua-duanya sebelum bisa menjawab ini. Salah satu kelompok jauh
lebih mahal daripada yang lain, dan kalau kamu salah menebak, kamu bakal benerin yang murah
lalu bingung kenapa masih lambat.

---

## Hint 2 — kenapa satu query bisa mahal

Anggap query kamu sudah turun ke 2. Query-nya sedikit. Kok masih ratusan milidetik?

Coba jalankan sendiri di database, di luar aplikasi:

```bash
make psql
```

```sql
EXPLAIN ANALYZE SELECT count(*) FROM comments WHERE post_id = 7;
```

Perhatikan kata `Seq Scan` dan berapa baris yang dibaca untuk menghasilkan satu angka.
Sekarang pertanyaannya: kenapa Postgres membaca jauh lebih banyak baris daripada yang kamu
butuhkan?

---

## Hint 3 — dua hal yang harus berubah, dan satu jebakan

Ada **dua** perbaikan, di dua tempat yang berbeda:

1. **Di aplikasi** — query per post harus jadi query yang dikelompokkan, bukan diulang.
   Untuk menghitung, kamu nggak butuh barisnya; kamu butuh agregatnya.
2. **Di database** — `comments.post_id` nggak punya index. Ini bagian yang biasanya
   diabaikan karena "kodenya sudah benar".

Kalau kamu baru mengerjakan nomor 1, `make check` akan menunjukkan satu baris masih merah.
Bagus — itu artinya kamu melihat masalah yang paling sering lolos ke produksi: kode yang
sudah diperbaiki di atas skema yang belum.

**Jebakan:** cara termudah "menghilangkan" query per post adalah memuat relasi komentarnya
sekaligus (`selectinload(Post.comments)`). Query-nya memang langsung jadi 2. Tapi sekarang
kamu memindahkan 25.000 baris dari database ke memori aplikasi hanya untuk menghitungnya.
Lihat apakah `make check` hijau. Kalau iya — periksa lagi, karena di dataset yang lebih
besar ini akan kembali meledak.

Index untuk produksi dibuat tanpa mengunci tabel:

```sql
CREATE INDEX CONCURRENTLY idx_comments_post_id ON comments (post_id);
```

Kenapa `CONCURRENTLY` penting di produksi, dan apa harganya? Itu pertanyaan untuk lab
berikutnya.
