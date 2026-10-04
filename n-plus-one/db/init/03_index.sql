-- Perbaikan kedua, dan yang paling sering terlewat: skema, bukan kode.

-- Tanpa index ini, "menghitung komentar per post" berarti membaca 750.000 baris
-- setiap kali halaman dimuat. Query-nya sudah benar; yang salah struktur datanya.

-- Di produksi tabel comments tidak kosong, jadi index harus dibuat tanpa mengunci tabel:
--
--   CREATE INDEX CONCURRENTLY idx_comments_post_id ON comments (post_id);
--
-- Di lab ini tabelnya milik kita sendiri dan tidak ada penulis lain saat initdb
-- berjalan, jadi bentuk biasa sudah cukup.

CREATE INDEX idx_comments_post_id ON comments (post_id);
