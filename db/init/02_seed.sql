-- Data "produksi": jumlahnya yang bikin masalahnya kelihatan.
-- 400 post, rata-rata ~500 komentar per post = 200.000 baris komentar.

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
FROM generate_series(1, 200000) g;

ANALYZE authors;
ANALYZE posts;
ANALYZE comments;
