# Solusi — pesan error yang menjawab "di mana, apa, harusnya bagaimana"

Untuk kamu yang sudah menyerah dan mau tahu jawabannya, atau yang ingin memverifikasi.

## Hasil pengukuran

Semua baris di bawah diukur dengan `scripts/check.py` yang sama, di mesin yang sama, apa adanya
(tanpa mengubah `data/` atau `scripts/check.py`).

| varian | hijau | catatan |
|---|---|---|
| kondisi awal (branch `main`) | **1 dari 7** | hanya A hijau: `periksa()` melempar `int(baris[2])` dan siapa pun yang memanggilnya berhenti di situ |
| semua masalah dikumpulkan, nomor baris `start=2`, kode keluar 0/1/2 | **7 dari 7** | — |

Angka konkret dari `make demo` di kondisi awal:

- `data/contoh/beberapa.csv` → `ValueError: invalid literal for int() with base 10: 'dua puluh'`,
  **0 dari 4** masalah dilaporkan, kode keluar `1`.
- `data/contoh/kosong.csv` → tidak ada keluhan, `3 baris diimpor`, kode keluar `0` (padahal ada
  baris tanpa nama).
- `data/contoh/kolom.csv` → `IndexError: list index out of range`, **0 dari 2** masalah dilaporkan.
- `data/contoh/tidak-ada.csv` → `FileNotFoundError`, kode keluar `1` (bukan `2`).

Di branch `solusi`, `make demo` menghasilkan satu baris laporan per masalah — empat untuk
`beberapa.csv`, dua untuk `kolom.csv` — dan kode keluar `0`/`1`/`2` sesuai keadaan.

## Kenapa kondisinya begini

**1. `periksa()` mencetak, bukan mengembalikan — dan melempar di tengah jalan.**

```python
umur = int(baris[2])   # ValueError kalau isinya bukan angka
if umur < 1 or umur > 120:
    print("umur tidak masuk akal, dilewati")
```

Dua cacat sekaligus. Pertama, `int()` melempar, dan `main()` tidak menangkapnya: satu baris jelek
menghentikan seluruh proses, jadi masalah setelahnya tidak pernah dilaporkan. Kedua, satu-satunya
diagnostik adalah `print` yang tidak menyebut baris maupun kolomnya. Komentar di atasnya justru
membenarkan keduanya ("Python sudah memberi pesan yang jelas", "yang bikin sistem rusak cuma
umur") — itulah perangkapnya: kodenya **terlihat** hati-hati.

**2. Nomor baris itu urusan yang memanggil, bukan yang memvalidasi.**

Fungsi `periksa` sebaiknya **mengembalikan daftar masalah** dan tidak tahu apa-apa soal nomor
baris; `main()` yang menempelkan `enumerate(pembaca, start=2)`. `start=2` bukan detail sepele:
baris 1 file adalah judul, jadi baris data pertama ada di baris 2. `start=1` menghasilkan angka
yang salah persis satu dari yang dilihat pengguna di editornya — dan bug itu lolos dari mata
sendiri karena "kelihatannya benar".

**3. `IndexError` sama saja belum memvalidasi.**

`data/contoh/kolom.csv` punya baris dengan 2 kolom dan 4 kolom. Menyentuh `baris[2]` sebelum
memastikan jumlah kolomnya cukup hanya memindahkan crash. Periksa jumlah kolom dulu, laporkan
sebagai satu masalah di kolom `jumlah kolom`, lalu jangan lanjut memeriksa isi baris itu.

**4. Kode keluar adalah bagian dari kontrak, bukan dekorasi.**

Script dipanggil dari `make`, `cron`, atau pipa shell. Pemanggil tidak membaca layar; dia membaca
kode keluar. "File tidak ada" (`2`) dan "file ada tapi isinya ada yang salah" (`1`) harus bisa
dibedakan — kalau tidak, script otomatis tidak akan tahu harus memanggil ulang, berhenti, atau
melanjutkan.

## Bentuk solusinya

```python
def periksa(baris):
    masalah = []
    if len(baris) != len(KOLOM):
        masalah.append(("jumlah kolom", f"... ketemu {len(baris)}, seharusnya {len(KOLOM)} ..."))
        return masalah
    nama, email, umur = (sel.strip() for sel in baris)
    if not nama:
        masalah.append(("nama", "kolom nama kosong, padahal harus diisi"))
    if "@" not in email:
        masalah.append(("email", f"'{email}' bukan alamat email karena tidak ada tanda '@' ..."))
    try:
        umur_angka = int(umur)
    except ValueError:
        masalah.append(("umur", f"'{umur}' bukan angka — isi dengan bilangan bulat, misalnya 25"))
    else:
        if not (UMUR_MIN <= umur_angka <= UMUR_MAX):
            masalah.append(("umur", f"{umur_angka} di luar rentang {UMUR_MIN}-{UMUR_MAX} ..."))
    return masalah
```

dan di `main()`:

```python
for nomor, baris in enumerate(pembaca, start=2):   # baris 1 file = judul
    for kolom, pesan in periksa(baris):
        sys.stderr.write(f"baris {nomor}: {kolom} — {pesan}\n")
```

Kode lengkapnya ada di `app/impor.py` di branch ini. Bedanya dengan `main`: validasi mengumpulkan
alih-alih melempar, nomor baris dihitung dari baris file, tiap masalah menyebut kolom + nilai
jelek + harapan, dan `main` mengembalikan `0`/`1`/`2`.
