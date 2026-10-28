# Hints

Buka satu per satu. Tiap hint cuma kasih pertanyaan berikutnya, bukan jawabannya.

---

## Hint 1 — kenapa meja 3 ikut dapat pesanan meja 1

Jalankan `make demo`. Tiga meja dibuka, tiap meja pesan satu barang. Lihat isi nota ketiga
meja: mereka punya item yang sama, padahal mereka meja yang beda.

Fokus ke satu fungsi dulu: `pesanan_baru`. Pertanyaan:

1. List item di dalam satu nota itu datang dari mana? Dia dibuat di mana, dan berapa kali?
2. Nilai default sebuah parameter di Python dihitung **sekali** waktu fungsinya baru
   didefinisikan, atau tiap kali fungsinya dipanggil? Buktikan jawabanmu: panggil
   `pesanan_baru(1)` dua kali, lalu cek `pesanan_baru(1)["item"] is pesanan_baru(2)["item"]`.
3. Kalau jawabannya "satu benda yang sama terus", kenapa penulis aslinya nulis `item=[]`?
   Apakah dia menyadari bedanya?

---

## Hint 2 — nota yang bilang totalnya Rp0

Hijaukan dulu kelompok 1, baru lanjut. Sekarang lihat `make check` lagi: kelompok 2 masih
merah, dan `total` tiap nota tetap Rp0 walaupun itemnya sudah benar.

Fokus ke fungsi `tambah_item`. Pertanyaan:

1. Baris `total = pesanan["total"]` itu bikin apa? `total` di situ menunjuk ke benda yang
   sama dengan `pesanan["total"]`, atau cuma menyalin nilainya?
2. Baris berikutnya, `total = total + harga * qty` — yang berubah di situ `pesanan` atau
   cuma nama lokal `total`?
3. Setelah `tambah_item` selesai, siapa pun yang memegang `pesanan` bakal lihat `total`
   yang mana? Kenapa?

Yang kamu nggak boleh lupa: nama variabel yang sama di dua tempat belum tentu benda yang
sama.

---

## Hint 3 — tiga keputusan

Semuanya satu tema: **tulis dulu di kertas kamu sedang mengubah benda apa, lalu baru
sentuh nama yang benar.**

**1. `pesanan_baru` nggak boleh punya list di nilai default-nya.** Nilai default dihitung
sekali dan dipakai ulang selamanya. Ganti jadi `item=None`, lalu di dalam fungsi:

```python
if item is None:
    item = []
```

`if item is None` mengalahkan `item or []` di sini: `item or []` juga bikin list baru untuk
list kosong yang sengaja dikirim pemanggil, jadi dia bener di demo ini tapi salah di kasus
lain.

**2. `tambah_item` harus menulis ulang ke dalam nota, bukan ke nama lokal.**

```python
pesanan["total"] = pesanan["total"] + harga * qty
```

Bedanya halus: `total = pesanan["total"]` menyalin **nilai**; `pesanan["total"] = ...`
mengubah **benda** yang dipegang pemanggil. Nama lokal `total` mati begitu fungsinya
selesai.

**3. `catat_penjualan` harus bilang ke Python bahwa `TOTAL_KAS` itu milik modul.**

```python
global TOTAL_KAS
TOTAL_KAS = TOTAL_KAS + jumlah
```

Tanpa `global`, penugasan ke `TOTAL_KAS` di dalam fungsi bikin Python menganggap kamu lagi
bikin variabel lokal baru. Kalau kamu tulis `TOTAL_KAS = TOTAL_KAS + jumlah` tanpa `global`,
hasilnya malah `UnboundLocalError` — dan itu justru lebih bagus, karena errornya keliatan.
Penulis aslinya menghindarinya dengan lewat variabel `total` lain, dan itu yang bikin bug ini
senyap.

---

## Jebakan yang harus kamu hindari

**Ngitung cuma satu lapis.** Tiga lab pertama di repo ini sudah melatih: memperbaiki satu
masalah aja nggak cukup, `make check` tetap merah karena lapisnya beda-beda. Hint 1 sampai 3
menunjuk ke tiga tempat yang beda.

**"Ngamanin" dengan menyalin.** Godaannya: tambah `.copy()` di mana-mana supaya nggak ada
yang saling nimpa. Tapi `.copy()` cuma bikin wadah baru — kalau isinya benda yang bisa
berubah juga, salinanmu masih berbagi isi dengan aslinya. Sebelum nambah salinan, tanya dulu:
yang aku mau pisahkan itu wadahnya atau isinya?

**Ngganti nama variabel biar "beda".** Kalau di `tambah_item` kamu ganti `total` jadi
`total_nota` — bug-nya nggak hilang, dia cuma pindah nama. Yang salah bukan namanya, tapi
fakta bahwa kamu mengubah nama lokal dan bukan nilai di dalam dict.

**Ngehapus item dari list yang bocor biar "bersih" di akhir.** Itu nambal gejalanya di
`demo`, bukan di `kasir.py`. `make check` manggil `kasir.py` tanpa lewat `demo`, jadi bakal
tetap merah.
