# Lab 1 — Endpoint feed yang jalan di laptop, tumbang di produksi

Bagian dari repo [`inva-lab`](../README.md). Semua perintah di bawah ini dijalankan dari
direktori `n-plus-one/`.

```bash
make up      # nyalain db + API, seed 400 post dan 750.000 komentar
make bench   # lihat sendiri angkanya
make check   # target lab ini
```

Endpoint `GET /api/posts?limit=20` mengembalikan 20 post terbaru, lengkap dengan nama
penulis dan jumlah komentarnya. Di laptop dengan data dummy, endpoint ini kelihatan biasa
saja dan nggak ada yang salah dengan kodenya.

Di sini:

| | sekarang |
|---|---|
| query ke database per request | **41** |
| latency p95 | **~1.100 ms** |

Server tidak error. Tidak lambat di kasus tertentu saja. Dia konsisten lambat di setiap
request — dan itu yang bikin masalahnya nggak kelihatan di staging, karena staging-nya
kosong.

## Misi kamu

Bikin `make check` hijau:

- query per request **≤ 3**
- latency p95 **≤ 30 ms**

Satu syarat yang nggak bisa dinegosiasikan: **hasilnya harus tetap sama.** Bandingkan body
response sebelum dan sesudah perubahan. Kalau komentar yang seharusnya 1.875 jadi 0, kamu
belum selesai — kamu cuma memindahkan masalahnya.

Boleh mengubah apa saja, kecuali:

- kontrak response (`id`, `title`, `author`, `comment_count`)
- jumlah data di `db/init/02_seed.sql` — dataset ini titik soalnya, bukan variabelnya

## Soal angka 30 ms

Itu anggaran lab ini, bukan hukum alam. Angka itu dipilih supaya *dua lapis* masalah di
endpoint ini sama-sama wajib dibereskan — kalau kamu cuma mengerjakan salah satunya, satu
baris di `make check` tetap merah, dan itu memang tujuannya.

Supaya kamu nggak perlu percaya begitu saja: biaya endpoint ini sudah diukur di dua ukuran
dataset. 300.000 baris komentar → 36 ms. 750.000 baris → 60 ms. Hampir sebanding dengan
jumlah baris, bukan tetap. Kalau kamu mau membuktikannya sendiri, ubah seed jadi 3× lipat,
`make reset`, lalu `make bench` lagi.

## Di mana mulainya

Lihat header `X-Db-Query-Count` di setiap response. Itu alat ukur kamu.

```bash
make explain   # satu request, cuma header query count-nya
make psql      # masuk ke database, untuk EXPLAIN ANALYZE
```

Kalau kamu belum pernah pakai `EXPLAIN ANALYZE`, sekarang waktu yang tepat. Tapi jangan
asal pakai: tulis dulu dugaanmu, baru bandingkan dengan kenyataan.

## Sebelum buka jawabannya

Kalau macet, buka `HINTS.md` sesuai urutan. Jangan lompat ke hint 3.

- nyangkut 45 menit → hint 1
- nyangkut 90 menit → hint 2
- menyerah → hint 3, dan **tulis di mana kamu nyerah** — itu bagian dari lab ini, bukan
  kegagalan

Jangan buka branch `solusi` sebelum kamu benar-benar mentok.

## Kenapa ini ada

Di tutorial, kamu bikin endpoint, datanya 20 baris, response-nya 8 ms, selesai. Di
produksi, kode yang sama jalan di atas ratusan ribu baris, dan yang muncul bukan error —
cuma angka latency yang naik pelan-pelan sampai ada yang komplain.

Lab ini punya satu hal yang nggak ada di tutorial: **kode awalnya kelihatan sudah benar.**
Ada bagian di dalamnya yang sengaja ditulis dengan niat baik. Cari tahu kenapa niat baik
itu tetap menghasilkan 41 query dan 1,1 detik.

## Tulisan pendamping

- Masalahnya, versi tulisan: **[Query-nya Tinggal 2, Tapi Response-nya Masih 1 Detik](https://invasikode.com/p/query-tinggal-2-tapi-response-masih-1-detik)**
- Jawabannya juga ada di situs, di seri **[Lab](https://invasikode.com/s/lab)** — tapi sengaja
  cuma bisa kamu buka dari tautan di ujung artikel masalahnya. Kalau kamu nyasar ke sana
  duluan, situsnya bakal mengingatkanmu balik. Coba saja.
