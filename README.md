# Lab 1 — Endpoint feed yang "jalan di laptop, tumbang di produksi"

```bash
make up      # nyalain db + API, seed 400 post dan 200.000 komentar
make check   # target lab ini
```

Endpoint `GET /api/posts?limit=50` mengembalikan 50 post terbaru, lengkap dengan nama
penulis dan jumlah komentarnya. Di laptop dengan data dummy, ini kelihatan biasa saja.

Di sini, dengan data yang jumlahnya masuk akal (400 post, 200.000 komentar):

| | sekarang |
|---|---|
| query ke database per request | **91** |
| latency p95 | **~680 ms** |

Server tidak error. Server tidak lambat di kasus tertentu saja. Dia **konsisten lambat**,
di setiap request, dan itu yang bikin masalahnya nggak kelihatan di staging.

## Misi kamu

Bikin `make check` hijau:

- query per request **≤ 3**
- latency p95 **≤ 60 ms**

Satu syarat yang nggak bisa dinegosiasikan: **hasilnya harus tetap sama.** Bandingkan body
response sebelum dan sesudah perubahan. Kalau komentar yang seharusnya 500 jadi 0, kamu
belum selesai — kamu cuma memindahkan masalahnya.

Kamu boleh mengubah apa saja kecuali:

- kontrak response (`id`, `title`, `author`, `comment_count`)
- jumlah data di `db/init/02_seed.sql` — dataset ini titik soalnya, bukan variabelnya

## Di mana mulainya

Lihat header `X-Db-Query-Count` di setiap response. Itu alat ukur kamu.

```bash
make explain
```

Kalau kamu belum pernah pakai `EXPLAIN ANALYZE`, sekarang waktu yang tepat. Tapi jangan
asal pakai: tulis dulu dugaanmu, baru bandingkan dengan kenyataan.

## Sebelum buka jawabannya

Kalau macet, buka `HINTS.md` sesuai urutan. Jangan lompat ke hint 3.

- nyangkut 45 menit → hint 1
- nyangkut 90 menit → hint 2
- menyerah → hint 3, dan **tulis di mana kamu nyerah**. Itu bagian dari lab ini, bukan
  kegagalan.

Jangan buka branch `solusi` sebelum kamu benar-benar mentok.

## Kenapa ini ada

Di tutorial, kamu bikin endpoint, datanya 20 baris, response-nya 8 ms, selesai. Di
produksi, kode yang sama jalan di atas 200.000 baris, dan yang muncul bukan error — yang
muncul cuma angka latency yang naik pelan-pelan sampai ada yang komplain.

Lab ini punya satu hal yang nggak ada di tutorial: **kode awalnya kelihatan sudah benar.**
Ada bagian yang sengaja ditulis dengan niat baik. Cari tahu kenapa niat baik itu tetap
menghasilkan 91 query.
