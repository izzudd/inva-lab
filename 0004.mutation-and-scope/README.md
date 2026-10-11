# Lab 4 — Tiap nota di kafe ini isinya pesanan yang sama

Bagian dari repo [`inva-lab`](../README.md). Semua perintah di bawah ini dijalankan dari
direktori `0004.mutation-and-scope/`.

```bash
make demo    # ceritanya: tiga meja pesan, lihat notanya
make check   # target lab ini
```

Malam yang ramai. Barista buka tiga meja, tiap meja pesan satu barang. Lalu barista lapor:
**nota tiap meja isinya sama semua** — kopi, teh, roti, ketiganya — padahal tiap meja cuma
pesan satu barang. Dan tiap nota bilang totalnya **Rp0**. Rekap kas harian di ujung juga
Rp0, padahal seharian jualan.

Ini yang keluar waktu `make demo` dijalankan di mesin yang bikin lab ini:

| | sekarang |
|---|---|
| tiga meja (1, 3, 5), masing-masing pesan satu barang | tiap nota isinya **3 item yang sama**: `kopi x2, teh x1, roti x1` |
| total nota tiap meja | **Rp0** (harusnya meja 1 Rp30.000, meja 3 Rp8.000, meja 5 Rp12.000) |
| kas harian setelah tiga meja jualan | **Rp0** (harusnya Rp50.000) |
| `make check` | **6 dari 6** pemeriksaan merah |

Nggak ada error, nggak ada exception. Kodenya jalan sampai selesai, dan tiap fungsi
kelihatan masuk akal kalau dibaca sekilas. Masalahnya bukan di satu tempat — ada tiga, dan
masing-masing punya obat yang beda.

## Lab ini beda dari tiga lab sebelumnya

Lab `0001`–`0003` itu FastAPI + Postgres + Docker. Lab ini **bukan**. Lab ini cukup **Python
3 standar** — tanpa Docker, tanpa database, tanpa `pip install`.

Alasannya: lab ini untuk pembaca seri **Konsep Dasar Pemrograman**, yang mungkin baru
belajar Python dan belum punya Docker di mesinnya. Kalau kamu harus install Docker dulu
sebelum bisa mulai belajar, kamu berhenti di langkah nol. Jadi di sini kamu cuma butuh satu
hal: `python3` yang sudah ada di hampir semua mesin. Semua kode ada di satu file, `kasir.py`.

## Misi kamu

Bikin `make check` hijau. Tiga syarat:

1. **Tiap nota cuma punya isi pesanan meja itu.** Meja yang belum pesan apa-apa notanya
   tetap kosong. Dua meja yang pesan menu beda nggak boleh saling ketuker.
2. **Total nota dihitung dari itemnya.** Jumlah item dan qty-nya ikut dikalikan, bukan
   sekadar dibiarkan Rp0.
3. **Kas harian bertambah sebesar yang benar-benar terjual.** Jual Rp32.000 → kas naik
   Rp32.000.

Boleh mengubah apa saja di `kasir.py`, asal tiga fungsi publiknya tetap bisa dipanggil
dengan cara yang sama seperti sekarang — `pesanan_baru(meja)`, `tambah_item(pesanan, nama,
qty=1)`, `total_kas()`. Nama `MENU` juga dipakai `make demo`. `make check` memanggil
ketiganya persis seperti itu.

## Di mana mulainya

```bash
make demo    # ceritanya, bukan angkanya
make check   # lihat sendiri pemeriksaan mana yang merah
```

Terus buka `kasir.py` dan baca dari atas. Tiap fungsi punya komentar yang menjelaskan niat
penulisnya. Niatnya bagus. Cari tahu kenapa niat yang bagus tetap menghasilkan nota yang
salah.

## Sebelum buka jawabannya

Kalau macet, buka `HINTS.md` sesuai urutan. Jangan lompat ke hint 3.

- nyangkut 30 menit → hint 1
- nyangkut 60 menit → hint 2
- menyerah → hint 3, dan **tulis di mana kamu nyerah**

Jangan buka branch `solusi` sebelum kamu benar-benar mentok.

## Kenapa ini ada

Kebanyakan orang belajar "fungsi" dari contoh yang cuma dipanggil sekali. Di kenyataan,
fungsi dipanggil berkali-kali, dan dua hal yang jarang diajarkan justru yang bikin lab ini
rusak:

- **Nilai default sebuah fungsi dihitung sekali, bukan tiap panggil.** Kalau default-nya
  benda yang bisa berubah (list, dict), benda itu dibagi ke semua pemanggil — selamanya.
- **Menulis `x = ...` di dalam fungsi cuma menyentuh nama `x` di fungsi itu.** Kalau yang
  kamu mau ubah sebenarnya ada di luar (di dalam sebuah dict, atau di scope modul), kamu
  harus menyentuh benda atau nama yang benar.

Dua-duanya kelihatan sepele waktu kamu membacanya, dan baru kelihatan waktu kodenya
dipakai lebih dari sekali. Itu bedanya baca tutorial dengan mentok sendiri.

## Batas lab ini

- **Ini bukan pelajaran tentang class.** Di sini semua state-nya cuma dict dan variabel
  modul. Dunia nyata sering menyelesaikan masalah ini dengan class — tapi class cuma nama
  lain untuk hal yang sama: kamu tetap harus tahu benda mana yang kamu pegang dan mana yang
  kamu ubah.
- **Variabel global bukan jawaban yang selalu benar.** Di lab ini `TOTAL_KAS` global itu
  bentuk paling sederhana. Begitu ada lebih dari satu kasir jalan bersamaan, satu variabel
  global nggak cukup — dan itu cerita lab lain.
- **Nilai default yang salah bukan satu-satunya jebakan "sekali".** Hal yang sama berlaku
  buat cache, koneksi, dan apa pun yang dibangun waktu modulnya pertama diimpor.
