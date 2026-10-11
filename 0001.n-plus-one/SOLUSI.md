# Solusi — dan kenapa ini bukan cuma soal N+1

Untuk kamu yang sudah menyerah dan mau tahu jawabannya, atau yang ingin memverifikasi.

## Hasil pengukuran

Semua baris di bawah ini diukur di mesin yang sama, dataset yang sama (400 post, 750.000
komentar, `limit=20`), dan **setiap varian mengembalikan body response yang identik**
(hash SHA-256-nya sama). Yang berubah cuma performanya.

| varian | query | p50 | p95 | lulus? |
|---|---|---|---|---|
| kondisi awal | 41 | 950 ms | 1.152 ms | tidak |
| penulis di-eager-load saja | 21 | 915 ms | 981 ms | tidak |
| jebakan: eager-load komentar + `len()` | **2** | 983 ms | 1.026 ms | tidak |
| agregat `GROUP BY`, tanpa index | 2 | 60 ms | 62 ms | tidak |
| agregat `GROUP BY` + index | 2 | 7,4 ms | **8,3 ms** | **ya** |
| jebakan + index | 2 | 949 ms | 1.002 ms | tidak |

## Urutannya, dan kenapa urutannya penting

**1. Nama penulis — 20 query jadi 0 query tambahan. Hasilnya hampir nggak kelihatan.**

`post.author` memicu lazy load. Diperbaiki dengan `joinedload(Post.author)`.

Perhatikan baris kedua tabel: 41 → 21 query, dan latency cuma turun dari 950 ms ke 915 ms.
Kelompok query ini menyumbang sekitar **4%** dari total waktunya, karena pencariannya
berdasarkan primary key — pencarian termurah yang bisa dilakukan database.

Ini pelajaran pertama: **"N+1" bukan satu penyakit.** Menghitung query saja tidak
memberitahu kamu mana yang mahal. Ini juga alasan kenapa "ubah ke eager loading" — nasihat
standar di hampir semua artikel — bisa dikerjakan dengan benar dan tetap nggak menolong.

**2. Jumlah komentar — 20 query jadi 1. 2 query, tapi masih gagal.**

Query count-nya dikumpulkan jadi satu `GROUP BY`. Latency turun dari ~1.150 ms ke **~60 ms**
— perbaikan 19×, dan `make check` **tetap merah** di baris latency, karena targetnya 30 ms.

Ini pelajaran kedua, dan yang paling sering lolos ke produksi: kamu sudah memperbaiki
*kode*, dan sisa masalahnya ada di *skema*. `comments.post_id` tidak punya index, jadi
setiap agregat membaca 750.000 baris.

**3. Index di `comments(post_id)` — 62 ms jadi 8,3 ms.**

Ini pelajaran ketiga: dua perbaikan itu ada di dua tempat berbeda, dan mengerjakan salah
satu saja menghasilkan perbaikan yang menipu. Kalau kamu hanya melihat jumlah query, kamu
akan mengira sudah selesai di langkah 2.

## Jebakan yang sengaja dibiarkan

Cara tercepat membuat query jadi 2 adalah `selectinload(Post.comments)`, lalu `len()`. Ini
sangat menggoda karena eager loading *memang* jawaban yang benar untuk N+1 — di kasus lain.

Yang terjadi: 20 post × ~1.875 komentar = **37.500 baris** dipindahkan dari database ke
memori aplikasi cuma untuk dihitung. Hasilnya 1.026 ms — hampir sama lambatnya dengan
kondisi awal, dengan jumlah query yang terlihat sempurna.

Dan perhatikan baris terakhir tabel: **menambahkan index pun nggak menolong jebakan ini**
(1.002 ms). Index mempercepat cara database *mencari*. Kalau masalahnya adalah jumlah data
yang harus *menyeberang*, index bukan jawabannya.

Menghitung bukan butuh datanya. Butuh angkanya.

## Pertanyaan buat kamu

1. Kenapa index `comments(post_id)` tidak menolong jebakan `selectinload`?
2. Kalau tabel `comments` punya 200 juta baris dan sedang ada trafik tulis, apa yang
   berubah dari langkah 3? Kenapa `CONCURRENTLY` penting, dan apa yang dikorbankan?
3. Kalau endpoint ini dipanggil 100 kali per detik, pada lapisan mana kamu pertama kali jadi
   bottleneck — dan metrik apa yang bakal memberi tahu kamu sebelum ada yang komplain?
4. Dari tiga kelompok query di kondisi awal, kenapa satu kelompok berbiaya ~4% dan yang lain
   ~96%? Jawab tanpa mengukur, lalu verifikasi.
