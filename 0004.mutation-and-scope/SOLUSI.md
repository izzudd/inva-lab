# Solusi — Lab 4: tiap nota isinya sama, total Rp0, kas Rp0

Jangan baca ini sebelum kamu mentok. Yang ada di sini bukan "kodenya salah di baris X".
Yang ada di sini adalah **cara berpikirnya**, supaya lain kali kamu nemu sendiri.

`git diff main solusi -- 0004.mutation-and-scope/` menunjukkan semua perubahannya. Di bawah
ini alasan tiap perubahan.

## Satu kalimat

Tiga lapis, satu tema: **mana yang kamu ubah, dan benda apa itu sebenarnya.** Setiap bug
muncul karena penulisnya mengira dia mengubah satu benda, padahal dia mengubah benda lain
(atau nggak mengubah apa pun).

## Lapis 1 — nilai default yang dihitung sekali

```python
def pesanan_baru(meja, item=[]):   # salah
```

Nilai default sebuah fungsi dihitung **sekali**, waktu fungsinya baru didefinisikan di
memori — bukan tiap kali dipanggil. Jadi `[]` di situ bukan "list kosong baru tiap panggil",
tapi "satu list yang sama, dipakai ulang selamanya". Semua nota berbagi list itu.

```python
def pesanan_baru(meja, item=None):   # benar
    if item is None:
        item = []
    return {"meja": meja, "item": item, "total": 0}
```

Cek sendiri:

```python
kasir.pesanan_baru(1)["item"] is kasir.pesanan_baru(2)["item"]   # harus False
```

Cara membuktikannya nggak perlu percaya kata orang: `pesanan_baru.__defaults__` menyimpan
list itu secara harfiah. Isi sebuah nota lalu lihat `pesanan_baru.__defaults__` — item yang
baru kamu masukkan muncul di situ juga, karena `pesanan["item"]` dan nilai default itu
**benda yang sama**:

```python
p = kasir.pesanan_baru(1)
kasir.tambah_item(p, "kopi", 1)
pesanan_baru.__defaults__   # ([{'nama': 'kopi', 'qty': 1, 'harga': 15000}],)
```

Perhatikan juga: `pesanan_baru` sendiri nggak pernah menambah apa-apa ke list itu. Yang
menambah adalah `tambah_item` — dan tetap saja list itu bertambah, karena cuma ada satu.

## Lapis 2 — mengubah nama lokal, bukan nilai di dalam dict

```python
total = pesanan["total"]        # menyalin NILAI
total = total + harga * qty     # cuma nama lokal yang berubah
return pesanan                  # nota nggak pernah tahu
```

`total = pesanan["total"]` bikin nama baru `total` yang menunjuk ke angka yang sama. Baris
berikutnya mengubah nama `total` itu jadi angka baru — tapi `pesanan` masih memegang angka
lama. Nama lokal mati begitu fungsinya selesai.

```python
pesanan["total"] = pesanan["total"] + harga * qty   # benar
```

Di sini yang diubah adalah **isi dict yang dipegang pemanggil**. Kalau `pesanan` adalah dict
(benda yang bisa berubah), mengubah isinya terlihat oleh semua yang memegang dict itu.

## Lapis 3 — variabel modul vs variabel fungsi (scope)

```python
TOTAL_KAS = 0

def catat_penjualan(jumlah):
    total = TOTAL_KAS        # bikin nama lokal "total"
    total = total + jumlah   # cuma lokalnya yang berubah
    return total             # TOTAL_KAS nggak pernah tersentuh
```

Penulis aslinya berhenti di tengah: dia niatnya nambah ke `TOTAL_KAS`, tapi nulisnya lewat
variabel lain. Akibatnya `TOTAL_KAS` tetap 0.

Kalau dia langsung tulis begini tanpa `global`:

```python
def catat_penjualan(jumlah):
    TOTAL_KAS = TOTAL_KAS + jumlah   # UnboundLocalError
```

Python malah melempar `UnboundLocalError`. Sebabnya: penugasan ke sebuah nama di dalam
fungsi bikin Python menganggap nama itu **lokal** untuk seluruh fungsi itu. Jadi waktu dia
baca `TOTAL_KAS` di sebelah kanan, Python belum menganggapnya ada.

```python
def catat_penjualan(jumlah):
    global TOTAL_KAS                 # benar
    TOTAL_KAS = TOTAL_KAS + jumlah
    return TOTAL_KAS
```

`global` bilang: nama `TOTAL_KAS` di sini menunjuk yang di scope modul, bukan yang baru di
sini.

## Cek sendiri setelah beres

```bash
make check    # harus 6 dari 6 LULUS
make demo     # tiga meja, tiga nota, sesuai pesanannya
```

`make demo` yang sudah beres:

```
  meja 1  isi: kopi x2
  meja 3  isi: teh x1
  meja 5  isi: roti x1

  meja 1  total nota: Rp30.000
  meja 3  total nota: Rp8.000
  meja 5  total nota: Rp12.000

Kas harian: Rp50.000
```

## Jebakan yang dilewati

- **Cuma memperbaiki lapis 1** (yang paling terkenal). `make check` tetap merah: kelompok 2
  dan 3 masih gagal. Diuji: memperbaiki lapis 1 saja menyisakan 4 dari 6 merah.
- **`item or []` sebagai ganti `if item is None`.** Bener di demo ini, salah begitu ada yang
  sengaja mengirim list kosong sebagai argumen — `item or []` menggantinya dengan list baru,
  padahal pemanggil mau mengisi list yang dia kirim.
- **Nambah `.copy()` di mana-mana.** `.copy()` bikin wadah baru, bukan isi baru. Kalau isinya
  benda yang bisa berubah juga, salinannya masih berbagi isi dengan aslinya.
- **Ganti nama variabel.** Mengganti `total` jadi `total_nota` nggak menghilangkan bug-nya,
  cuma memindahkannya. Yang salah bukan namanya, tapi fakta bahwa yang diubah adalah nama
  lokal dan bukan nilai di dalam dict.

## Konteks yang lebih luas

Masalah "nilai default dihitung sekali" nggak berhenti di list kosong. Hal yang sama berlaku
ke semua yang dibangun waktu modulnya pertama diimpor: cache, pool koneksi, konfigurasi yang
dibaca sekali. Dan "global vs lokal" adalah versi kecil dari pertanyaan yang lebih besar:
**siapa yang sebenarnya memegang state ini, dan berapa banyak pemegangnya.** Begitu jawabannya
"lebih dari satu", kamu butuh alat yang lebih serius daripada variabel global — dan itu
cerita lab berikutnya.
