# Hints

Buka satu per satu. Tiap hint cuma kasih pertanyaan berikutnya, bukan jawabannya.

---

## Hint 1 — script-nya mati di baris pertama yang jelek

Jalankan `make demo`. Lihat dua file yang bermasalah: yang satu berhenti dengan `ValueError`,
yang satu dengan `IndexError`. Dan `data/contoh/kosong.csv` malah tidak bilang apa-apa.

Tiga pertanyaan:

1. Buka `app/impor.py`. Baris `umur = int(baris[2])` itu apa yang terjadi kalau isinya bukan
   angka? Siapa yang menangkapnya? Kalau tidak ada yang menangkap, apa yang membuat seluruh
   program berhenti — dan berapa masalah yang **tidak** keburu dilaporkan?
2. Perhatikan komentar di fungsi `periksa` dan di dalam perulangan. Dua-duanya menjelaskan
   keputusan yang disengaja. Apakah alasan di komentarnya masih benar, kalau yang kamu
   inginkan adalah melaporkan semua baris jelek, bukan berhenti?
3. Sekarang `data/contoh/kosong.csv`: kenapa `make impor` bilang `3 baris diimpor` dengan
   tenang sementara ada baris tanpa nama? Kolom mana yang diperiksa, dan kolom mana yang
   dilewati?

Yang perlu kamu ubah dulu cuma satu: **satu baris jelek tidak boleh menghentikan seluruh
proses**, dan **setiap masalah harus jadi satu baris laporan**, bukan traceback.

---

## Hint 2 — "di mana" yang benar, dan kode keluar

Kalau semua masalah sudah dilaporkan, dua jebakan berikutnya yang paling sering kena:

1. **Nomor barisnya.** Kalau kamu menghitung dari baris data (`enumerate(data, start=1)`), angka
   itu **bukan** nomor baris di file. Baris 1 di file adalah judulnya. Coba `data/contoh/
   beberapa.csv` di editor: masalah pertama ada di baris berapa? Bandingkan dengan yang
   dilaporkan programmu. Kalau beda satu, kamu sedang menghitung index data, bukan baris file.
2. **`IndexError` di `data/contoh/kolom.csv`.** Baris yang jumlah kolomnya kurang atau lebih
   tidak bisa diperiksa isinya per kolom — sebelum menyentuh `baris[2]`, pastikan dulu jumlah
   kolomnya memang benar.
3. **Kode keluar.** Sekarang `FileNotFoundError` juga bikin kode keluar `1`, sama seperti file
   yang berisi data jelek. Dari sisi pemanggil, "file-nya tidak ketemu" dan "file-nya ketemu
   tapi isinya ada yang salah" itu dua hal yang sangat berbeda. Mana yang `0`, mana yang `1`,
   mana yang `2`?

---

## Hint 3 — bentuk akhirnya

Semuanya satu tema: **satu masalah = satu baris, dengan tiga bagian** (di mana, apa, harusnya
apa), dan **program tidak berhenti walau ada baris jelek**.

**1. Validasi jadi fungsi yang mengumpulkan, bukan yang melempar.** Buat `periksa(baris)`
mengembalikan **daftar** masalah, bukan mencetak atau `raise`. Baris yang benar mengembalikan
daftar kosong. Satu baris boleh punya lebih dari satu masalah (lihat baris 3 di
`beberapa.csv`: nama kosong **dan** email tanpa `@`).

**2. Periksa jumlah kolom lebih dulu.** Kalau `len(baris) != len(KOLOM)`, itu satu masalah di
kolom `jumlah kolom` — dan berhenti di baris itu saja, karena kolom per kolom belum bisa
dipercaya. Untuk masalah lain, `umur` beda dari yang lain: `int(umur)` bisa melempar
`ValueError`, jadi bungkus dengan `try/except` dan jadikan pesannya, misalnya `'"dua puluh"
bukan angka — isi dengan bilangan bulat, misalnya 25`.

**3. Nomor barisnya dari `enumerate(pembaca, start=2)`.** Mulai dari 2, karena baris 1 file
adalah judul. Ini yang bikin pemeriksaan D hijau.

**4. Tulis laporannya ke `stderr` dengan format yang tetap**
(`baris {nomor}: {kolom} — {pesan}`), lalu `return 1` kalau ada masalah, `0` kalau tidak.
Untuk file yang tidak ada atau argumen yang kurang, tulis satu baris penjelasan lalu `return 2`
— jangan biarkan traceback yang muncul.

---

## Jebakan yang harus kamu hindari

**Membungkus semuanya dengan satu `try/except` besar di `main`.** Itu memang menghilangkan
traceback, tapi juga menghentikan program di baris jelek pertama — pemeriksaan C tetap merah.
Yang benar: `try/except` kecil dan spesifik di tempat yang memang bisa gagal (`int(umur)`,
`open(path)`), sisanya jalan terus.

**Menyalin pesan Python apa adanya.** `invalid literal for int() with base 10` benar secara
teknis dan tidak berguna bagi pengguna. Yang dicari pengguna: baris berapa, kolom apa, nilainya
apa, dan harus diisi bagaimana.

**Lupa bahwa satu baris bisa punya dua masalah.** Kalau `periksa` mengembalikan setelah masalah
pertama, baris 3 di `beberapa.csv` cuma menghasilkan satu laporan, dan pemeriksaan C merah.
