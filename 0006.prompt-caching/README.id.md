# Lab 6 — Cache yang tidak pernah kena

Bagian dari repo [`inva-lab`](../README.md). Semua perintah di bawah dijalankan dari direktori
`0006.prompt-caching/`.

```bash
make demo     # tagihan sekarang, per tiket
make bench    # loop yang sama, per giliran (ID=T-1043 untuk satu tiket)
make check    # target lab ini
```

Kamu punya agen support yang menjawab tiket. Di dalam prompt-nya ada buku panduan enam ribu kata,
lima definisi tool, dan transkrip percakapan yang terus tumbuh. Prompt caching menyala: provider
sudah menyimpan prefix, model memberi jawaban yang sama, tetapi tagihannya tidak cocok dengan
hitungan token.

Ini yang muncul sekarang, apa adanya:

| perintah | yang terlihat sekarang |
|---|---|
| `make demo` | `hit=  0.0%  $0.4841` untuk ketiga tiket |
| `make check` | **0 dari 7** pemeriksaan hijau |
| loop yang sama dengan `cache_enabled=False` | `$0.4017` — **caching 21% lebih mahal daripada tidak caching** |

Tidak ada yang rusak dengan cara yang terlihat seperti stack trace. Semua tiket terjawab, loop
keluar dengan kode 0, dan provider tidak melaporkan apa pun yang aneh. Tagihannya saja yang salah,
dan satu-satunya yang memberi tahu adalah angka yang harus kamu cari sendiri.

## Kenapa tagihannya lebih tinggi daripada daftar harga

Cache hit bukan sifat dari fitur yang kamu nyalakan, melainkan sifat dari byte yang kamu kirim:
provider menghitung hash prefix sampai breakpoint yang kamu tandai, dan hanya bisa memakai entri yang
pernah **ditulis** oleh permintaan sebelumnya di batas yang akan dia periksa lagi kali ini. Satu byte
berubah di prefix, satu breakpoint di tempat yang salah, atau satu entri kedaluwarsa sudah cukup
untuk membayar harga tulis untuk seluruh prompt dan tidak mendapat apa pun.

Provider di lab ini menerapkan aturan satu vendor yang diterbitkan November 2026:

- entri cache **hanya** ditulis di blok yang kamu tandai sebagai breakpoint;
- pembacaan menelusuri mundur dari breakpoint, paling jauh **20 posisi blok**, dan memakai entri
  pertama yang benar-benar ditulis permintaan sebelumnya;
- prefix di bawah **512 token** tidak bisa di-cache sama sekali;
- **5 menit** secara bawaan, **1 jam** kalau kamu minta, dan diperpanjang gratis setiap kali dibaca;
- tulis dibayar **1,25x** harga input, baca dibayar **0,1x**.

`agent/provider.py` adalah aturan itu dalam bentuk program. Itu alat ukur, bukan latihannya: jangan
diubah. Sisanya di `agent/` milikmu.

## Misi

Buat `make check` hijau. Tujuh pemeriksaan di `scripts/check.py`, satu tema:

> Cache mengikuti byte. Urutkan prompt berdasarkan seberapa sering bagiannya berubah, taruh
> breakpoint di ujung bagian yang tidak berubah, dan ukur hit rate-nya daripada percaya pada saklar
> fiturnya.

Tiga syarat di balik tujuh pemeriksaan itu:

1. **Permintaan yang sama, dua kali, harus memakai ulang prefix-nya.** Sedikitnya 75% token yang
   kamu kirim kembali sebagai cache read, dan biayanya paling banyak 45% dari loop yang sama tanpa
   cache. Dua tiket berbeda tidak boleh merusak prefix satu sama lain.
2. **Model tetap harus menerima yang dia butuhkan.** Tanggal hari ini harus sampai ke model — memindahkannya keluar dari prompt bukan perbaikan. Array tool harus identik byte demi byte dari
   giliran pertama sampai terakhir, dan tiap permintaan harus merupakan permintaan sebelumnya
   ditambah blok baru, bukan penulisan ulang blok lama.
3. **Loop harus bertahan melewati jeda, dan mengatakannya.** Pelanggan diam sepuluh menit setelah
   giliran keempat; giliran sesudahnya tetap harus membaca buku panduan dari cache. Dan
   `python3 agent/loop.py` harus mencetak satu baris berisi angka yang benar-benar dia ukur:

   ```
   summary turns=24 hit_rate=0.909 cost_usd=0.143682
   ```

`make bench` adalah cara melihat bentuk masalahnya sebelum menyentuh apa pun: per giliran ia
mencetak berapa token dikirim, berapa dibaca dari cache, berapa ditulis, dan berapa biayanya.

## Di mana biaya yang kamu kejar

Prefix statis — buku panduan ditambah definisi tool — adalah 6.135 token; transkrip tumbuh sekitar
320 token per giliran. Dalam delapan giliran, blok statis mendominasi setiap permintaan, jadi
meng-cache-nya dengan benar bernilai lebih besar daripada memendekkannya — tetapi hanya selama
transkrip masih tipis. Lewat sepuluh giliran, transkrip yang mendominasi dan buku panduan berhenti
menjadi tuasnya. `make bench` menampilkan keduanya di baris yang sama, dan itulah intinya.

## Yang tidak dilakukan lab ini

- **Tidak memanggil provider sungguhan.** Tanpa kunci, tanpa jaringan, tanpa tagihan. Mesinnya
  simulasi deterministik dari aturan satu vendor, jadi angkanya bisa diulang dan gratis; angkanya
  juga **bukan** yang akan ditagih ke akunmu. Artikel pendampingnya memuat angka yang tidak
  disimulasikan.
- **Satu token di sini adalah satu kata dipisah spasi.** Cukup dekat untuk dokumen 6.000 kata, tidak
  cukup dekat untuk memprediksi invoice sungguhan.
- **Hanya memodelkan prefix caching.** Tanpa batch, tanpa token reasoning, tanpa streaming, tanpa
  sticky routing.

## Di mana jawabannya

Semua jawaban ada di branch **`solusi`**:

```bash
git diff main solusi -- 0006.prompt-caching/
```

Baca [`HINTS.id.md`](HINTS.id.md) dulu. Ada tiga tingkat, dan tingkat pertama sudah cukup untuk
kebanyakan orang.
