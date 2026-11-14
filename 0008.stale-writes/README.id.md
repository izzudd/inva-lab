# Lab 8 — Stok yang datang tidak berurutan

Bagian dari repo [`inva-lab`](../README.md). Semua perintah di bawah dijalankan dari direktori
`0008.stale-writes/`.

```bash
make demo   # yang diyakini sistem, di sebelah hitungan gudang
make run    # setiap pesan sesuai urutan kedatangan, satu baris per pesan
make check  # target lab ini
```

Kamu memegang layanan stok untuk toko online kecil. Perubahan stok masuk sebagai pesan: petugas gudang
memindai rak lalu mengirim `set`, pembeli membeli lalu toko mengirim `sale`. Satu queue, satu
consumer, tanpa konkurensi, dan setiap pesan langsung diterapkan begitu tiba.

Ini yang muncul sekarang, apa adanya:

| perintah | yang terlihat sekarang |
|---|---|
| `make demo` | `CAP-03 -1` sedangkan gudang `0`, `MUG-01 4` sedangkan gudang `6`, `TEE-02 11` sedangkan gudang `9` |
| `make check` | **1 dari 5** pemeriksaan hijau |
| `make run` | 11 pesan, `summary messages=11 applied=11 rejected=0` |

Topi yang stoknya nol tetap terjual. Mug terbaca empat padahal di rak ada enam. Tidak ada yang
melempar error, queue kosong dengan rapi, ringkasannya pun rapi, dan satu-satunya yang salah adalah
angka yang tidak pernah dibandingkan dengan rak.

## Kenapa satu queue menghasilkan tiga rak yang salah

Setiap pesan membawa jumlah **pada saat kejadiannya** di `event_time`, dan queue tidak menjanjikan
urutan itu. Tiga dari sebelas pesan di `data/messages.json` tiba lebih lambat daripada kejadian yang
mereka gambarkan:

- **MUG-01** — `e-104` bilang enam pada 10:10, lalu `e-102` bilang empat pada 10:05 datang setelahnya.
  Angka yang lebih tua mendarat terakhir dan menang, jadi rak terbaca empat.
- **TEE-02** — bentuk yang sama dengan sebelas dan sembilan: hitung ulang 10:09 ditimpa pesan 10:08
  yang tiba setelahnya.
- **CAP-03** — tiga topi, dua terjual, lalu hitung ulang nol, lalu satu penjualan lagi pada 10:14.
  Penjualan itu membawa rak ke minus satu, dan toko terus menjual topi yang tidak ada.

Semuanya masuk akal saat dibaca di code review. Consumer menerapkan apa yang dikatakan pesan, dan
pesannya tidak salah: pesannya tua. Queue tidak punya pendapat soal waktu.

## Misi kamu

Bikin `make check` hijau. Lima pemeriksaan di `scripts/check.py`, satu tema:

> Pesan tentang masa lalu tidak boleh menimpa masa kini, dan penjualan tidak boleh membawa rak di
> bawah nol.

Dua pemeriksaan membaca `data/warehouse.json`, hasil hitung manual jam 18:00. Tiga lainnya menjalankan
queue kecilnya sendiri, jadi mengubah file data tidak bisa membuatnya hijau:

- **A** jumlah setiap produk sama dengan hitungan gudang;
- **B** update yang lebih tua dari `event_time` tersimpan ditolak, bukan diterapkan;
- **C** tidak ada jumlah negatif, dan penjualan di rak kosong ditolak;
- **D** event yang dikirim ulang tidak menggeser stok;
- **E** consumer mencetak `summary messages=11 applied=N rejected=M` sesuai yang benar-benar ia
  terapkan, jadi baris terakhir tidak bisa berbohong soal isi di atasnya.

Versi jawaban lolos kelimanya dan mencetak `summary messages=11 applied=8 rejected=3`: tiga dari
sebelas pesan menggambarkan keadaan yang sudah lewat.

## Yang sudah benar di versi awal

Pelaporannya. `make run` mencetak satu baris per pesan dan ringkasan yang cocok dengan penghitung
milik store, karena itulah satu-satunya pemeriksaan yang hijau sebelum kamu menyentuh apa pun.
Consumer yang melapor jujur sambil menerapkan membabi buta adalah kasus biasa: log memberi tahu apa
yang ia lakukan, bukan apa yang seharusnya ia lakukan.

## Yang tidak dikerjakan lab ini

- **Tanpa broker.** Queue-nya array JSON dalam urutan kedatangan. Broker sungguhan memungkinkan kamu
  menguji prefetch dan pengiriman ulang; di sini keduanya ditulis di dalam file.
- **Tanpa konkurensi.** Satu proses, satu jalur. Menyerialkan pesan akan membuat hasilnya
  deterministik sekaligus menyembunyikan masalahnya, dan itulah jebakan yang sengaja dipasang: solusi
  harus tetap benar saat ada dua worker, jadi tidak boleh berupa "terapkan sesuai urutan yang benar".
- **Tanpa push ke storefront.** Jalur ketiga di cerita aslinya (retry push ke sistem lain) di luar
  cakupan. Apakah perlu storefront tiruan di lab ini masih keputusan terbuka.
- **Kosakata hanya `set` dan `sale`.** Tidak ada reservasi, transfer antar gudang, atau retur.

## Di mana jawabannya

Jawaban yang berjalan ada di branch **`solusi-0008-stale-writes`**:

```bash
git diff main solusi-0008-stale-writes -- 0008.stale-writes/
```

Baca [`HINTS.id.md`](HINTS.id.md) dulu. Ada tiga tingkat, dan tingkat pertama cuma meminta kamu
meletakkan dua pesan berdampingan.
