# Lab 5 — Script yang nggak bisa bilang di mana salahnya

Bagian dari repo [`inva-lab`](../README.md). Semua perintah di bawah ini dijalankan dari
direktori `0005.error-messages/`.

```bash
make demo    # lihat yang dilihat pengguna di tiap file contoh
make check   # target lab ini
make impor FILE=data/contoh/beberapa.csv   # jalankan importer sekali
```

Kamu punya script kecil: `app/impor.py` membaca file `.csv` berisi daftar pendaftar
(`nama,email,umur`) dan menyimpan baris yang valid. Selama file-nya kamu bikin sendiri, semua
baik-baik saja. Begitu file datang dari tim lain, telepon mulai berdering:

- **Beberapa file bikin script-nya mati mendadak dengan `Traceback` di layar**, dan yang
  dilaporkan cuma baris yang kebetulan bikin dia tersandung lebih dulu — sisanya tidak pernah
  disebut.
- **File lain sebaliknya: tidak ada keluhan apa pun**, padahal di dalamnya ada baris yang
  jelas rusak.
- **Yang minta tolong mengeluh**: "aku nggak tahu baris berapa yang salah, kolom apa, dan aku
  harus ngapain." Traceback menyebut nama variabel Python, bukan baris di file mereka.

Ini yang terjadi di lab ini (angka dari `make demo` dan `make check`, dijalankan apa adanya):

| perintah | yang muncul sekarang |
|---|---|
| `make impor FILE=data/contoh/beberapa.csv` | `ValueError: invalid literal for int() ... 'dua puluh'` — **0 dari 4** masalah dilaporkan |
| `make impor FILE=data/contoh/kosong.csv` | tidak ada keluhan, dan bilang `3 baris diimpor`, kode keluar `0` |
| `make impor FILE=data/contoh/kolom.csv` | `IndexError: list index out of range` — **0 dari 2** masalah dilaporkan |
| `make impor FILE=data/contoh/tidak-ada.csv` | `FileNotFoundError`, kode keluar `1` |
| `make check` | **1 dari 7** pemeriksaan hijau (Cuma A) |

## Kenapa labnya beda dari 0001–0003

Lab 0001 sampai 0003 level produksi: FastAPI, Postgres, Docker, dan target performanya. Lab ini
sengaja level pemula, untuk pembaca seri **Konsep Dasar Pemrograman**: cukup **Python 3 pakai
pustaka standar**. **Tidak perlu Docker**, **tidak perlu database**, tidak perlu `pip install`
apa pun — di mesin ini jalan dengan `python3` yang sudah ada (diuji dengan Python 3.12.3). Yang
kamu latih di sini bukan kecepatan atau concurrency, tapi satu hal yang dipakai di semua bahasa:
**membuat program yang salahnya bisa dibaca manusia.**

## Misi kamu

Bikin `make check` hijau. Tujuh pemeriksaan (A–G) di `scripts/check.py`, satu tema:

> Pesan error yang berguna menjawab tiga hal: **di mana**, **apa yang salah**, dan
> **harusnya bagaimana**. Program yang berhenti di masalah pertama baru menjawab satu.

Tiga syarat besarnya:

1. **Laporkan semuanya, jangan mati di yang pertama.** Untuk file dengan empat masalah, keempatnya
   dilaporkan — dan tidak ada `Traceback` Python yang bocor ke pengguna. File bersih tidak
   mengeluh sama sekali.
2. **Tiap laporan menyebut di mana dan apa.** Nomor baris **di file** (bukan index baris data),
   nama kolom yang salah, nilai jeleknya, dan apa yang diharapkan. Satu masalah = satu baris,
   formatnya:

   ```
   baris <nomor>: <kolom> — <apa yang salah, nilainya, dan yang diharapkan>
   ```

3. **Kode keluar membedakan tiga keadaan**, bukan satu kode untuk semua: `0` = beres, `1` = ada
   baris bermasalah, `2` = caranya yang salah (file tidak ada, argumen kurang).

Boleh mengubah `app/` sesukamu. Yang **jangan** diubah: `scripts/check.py` (itu penilainya),
`data/` (fixture-nya, termasuk `data/contoh/`), dan `Makefile`.

## Di mana mulainya

```bash
make demo     # ceritanya dulu: apa yang dilihat pengguna di tiap file
make bantu    # daftar perintah
```

File contohnya sengaja kecil dan jelek dengan cara yang beda-beda:

- `data/contoh/kosong.csv` — ada baris tanpa nama
- `data/contoh/beberapa.csv` — beberapa baris bermasalah sekaligus, satu baris bahkan punya dua
  masalah
- `data/contoh/kolom.csv` — ada baris dengan jumlah kolom yang tidak cocok dengan judulnya
- `data/pendaftar.csv` — file bersih, buat pembandingnya

## Sebelum buka jawabannya

Kalau macet, buka `HINTS.md` sesuai urutan. Jangan lompat ke hint 3.

- nyangkut 20 menit → hint 1
- nyangkut 40 menit → hint 2
- menyerah → hint 3, dan **tulis di mana kamu nyerah**

Jangan buka branch `solusi` sebelum kamu benar-benar mentok.

## Kenapa ini ada

Waktu seorang pemula menulis validator, yang paling sering terlewat bukan validasinya — tapi
laporannya. Kodenya `raise ValueError` dan menyangka pesan Python itu sudah cukup. Di laptop
sendiri, cukup. Di tangan orang lain, `ValueError: invalid literal for int() with base 10:
'dua puluh'` tidak memberi tahu **baris berapa di file** yang bermasalah. Pesan error adalah
satu-satunya bagian program yang dibaca orang yang sedang panik. Menulisnya bukan pekerjaan
tambahan; itu bagian dari pekerjaannya.

## Batas lab ini

- **Error yang dibahas semuanya "data salah", bukan "program salah".** Di sini kamu memvalidasi
  masukan. Error karena bug di kodemu sendiri (misal logika salah) cerita yang lain lagi.
- **Ini program satu kali jalan, bukan layanan.** Kode keluar (`exit code`) penting karena
  script dipanggil dari `cron`, `make`, atau pipa; di sebuah layanan, "di mana" bisa berarti
  field di body request, bukan nomor baris.
- **Belum tahan skala besar.** Format `baris N: kolom — pesan` cukup untuk ukuran file seperti ini. Begitu
  filenya ratusan megabyte, melaporkan semuanya sekaligus juga punya ongkosnya.
