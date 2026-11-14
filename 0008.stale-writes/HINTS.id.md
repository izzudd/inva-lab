# Petunjuk

Buka satu per satu. Setiap petunjuk hanya memberi pertanyaan berikutnya, bukan jawabannya.

---

## Petunjuk 1 — dua baris, satu produk

`make run` mencetak sebelas baris. Lihat baris 2 dan 3:

```
 2  e-104  MUG-01  set    6  @10:10  applied   MUG-01 = 6
 3  e-102  MUG-01  set    4  @10:05  applied   MUG-01 = 4
```

Pesan yang datang kedua menggambarkan 10:05. Pesan sebelumnya menggambarkan 10:10. Mana yang berita,
dan mana yang sejarah yang tiba terlambat?

Sekarang pertanyaan yang sama untuk CAP-03: kelima barisnya menggeser produk itu, termasuk yang
terakhir, yang terjadi setelah rak sudah dihitung nol. Baris mana yang seharusnya ditolak?

---

## Petunjuk 2 — baris butuh ingat kapan angkanya benar

1. **Store hanya menyimpan jumlah per SKU dan tidak lebih.** `self.rows[sku]` sudah punya field
   `event_time`, dan `apply()` menimpanya di setiap pesan. Dua pesan, satu field: store tahu nilai
   pesan terakhir yang ia terapkan, bukan waktu fakta terbaru yang ia pegang. Apa yang harus ia
   bandingkan sebelum menulis?
2. **`sale` mengurangi tanpa melihat.** Di cabang penjualan cuma ada satu baris, dan baris itu tidak
   menanyakan apakah rak sanggup menutup penjualan itu. Pemeriksaan C menjalankan queue kecilnya
   sendiri (`one item, then two sales`), jadi isi `data/messages.json` tidak berpengaruh.
3. **Tidak ada yang mencatat apa yang sudah diproses.** Pemeriksaan D mengirim `e-302` dua kali dan
   mengharapkan stok tidak bergeser. Apa di dalam pesan yang menandai **event**-nya, bukan isinya?

---

## Petunjuk 3 — satu penjaga, dengan urutan yang benar

`apply()` butuh tiga pertanyaan sebelum menulis, dan urutannya penting:

1. **Apakah `event_id` ini sudah pernah kulihat?** Kalau ya, tolak: berita yang sama dua kali tetap
   satu fakta.
2. **Apakah pesan ini lebih tua dari `event_time` di baris?** Kalau ya, tolak dan hitung sebagai tua.
   Penjaga inilah yang mengubah "pesan terakhir menang" menjadi "fakta terbaru menang".
3. **Apakah ini penjualan yang lebih besar dari isi rak?** Kalau ya, tolak. Penjualan bukan `set`
   dengan tanda minus, karena `set` menggambarkan keadaan sedangkan penjualan menggambarkan jumlah
   yang harus benar-benar ada.

Setelah ketiganya, penulisannya sama seperti sebelumnya. Lalu penghitung di `summary()` harus jujur:
`applied` adalah yang kamu tulis, `rejected` adalah yang kamu tolak, dan jumlahnya harus sama dengan
semua pesan yang kamu baca. Pemeriksaan E membandingkan baris itu dengan penghitung store, jadi
ringkasan yang menghitung semuanya sebagai `applied` akan gagal begitu kamu mulai menolak sesuatu.

Kalau `make check` bilang `B` masih merah, lihat apa yang dilakukan `clock()`: membandingkan string
langsung berhasil untuk file data ini dan rusak pada hari sebuah pesan membawa offset zona waktu.
