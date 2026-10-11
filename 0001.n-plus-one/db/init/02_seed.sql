-- Data "produksi": jumlahnya yang bikin masalahnya kelihatan.
-- 400 post, rata-rata ~1.900 komentar per post = 750.000 baris komentar.
--
-- Jumlah komentar ini titik soalnya, bukan variabel yang bisa diakali.
-- Kalau kamu mau membuktikan bahwa biaya di endpoint ini tumbuh mengikuti
-- jumlah baris, kalikan angka 750000 di bawah, lalu `make reset`.

INSERT INTO authors (name)
SELECT 'Penulis ' || g FROM generate_series(1, 40) g;

INSERT INTO posts (author_id, title, body, created_at)
SELECT
    1 + (g % 40),
    'Kenapa sistem kami tumbang di hari ke-' || g,
    repeat('Isi tulisan yang panjangnya realistis. ', 40),
    now() - (g || ' minutes')::interval
FROM generate_series(1, 400) g;

INSERT INTO comments (post_id, author_name, body, created_at)
SELECT
    1 + (g % 400),
    'Komentator ' || (g % 900),
    'Komentar nomor ' || g,
    now() - (g || ' seconds')::interval
FROM generate_series(1, 750000) g;

ANALYZE authors;
ANALYZE posts;
ANALYZE comments;
