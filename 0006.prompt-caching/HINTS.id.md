# Petunjuk

Buka satu per satu. Tiap petunjuk hanya memberi pertanyaan berikutnya, bukan jawabannya.

---

## Petunjuk 1 — apa yang sebenarnya di-hash

`make what-changes` mencetak dua permintaan berurutan, blok demi blok. Jalankan.

Tiga pertanyaan:

1. Baris tools bertulis `DIFFERENT`. Field mana di dalam definisi tool yang berbeda antara giliran 1
   dan giliran 2 — dan apakah model membutuhkannya?
2. Blok `[0]` bertulis `CHANGED`, padahal jumlah katanya sama dua-duanya. Jadi teksnya bukan
   bertambah, melainkan *berbeda*. Apa di dalam `system_prompt()` yang bergantung pada jam?
3. Tanda ^ adalah breakpoint. Di permintaan 1 ia di blok `[1]`, di permintaan 2 ia di blok `[3]`.
   Provider hanya menulis entri **di tanda ^**, jadi tanyakan: prefix mana yang ditulis giliran 1,
   dan apakah giliran 2 pernah memeriksanya?

Tidak ada hal lain yang penting sampai ketiga pertanyaan itu punya jawaban yang sama: **blok pertama
setiap permintaan harus identik byte demi byte dengan blok pertama permintaan sebelumnya.**

---

## Petunjuk 2 — tiga baris, dan satu yang bukan baris prosa

1. **Tool adalah bagian dari prefix.** Provider mem-hash `tools` lalu blok-bloknya, jadi deskripsi
   tool yang ditulis ulang membatalkan semua yang ada sesudahnya, termasuk enam ribu kata buku
   panduan. Timestamp "registry snapshot" di definisi tool adalah timestamp di dalam prefix.
2. **Tanggal harus dipindah, bukan dihapus.** `make check` menggagalkan pemeriksaan C kalau prefix
   berubah antara dua hari *dan* menggagalkannya lagi kalau tanggalnya tidak pernah sampai ke model.
   Jadi jam berada di ujung permintaan — di giliran yang kamu kirim — bukan di dalam buku panduan.
3. **`make bench`, giliran 3 dan 4.** Jumlah token tumbuh ~320 per giliran, lalu hampir tidak
   tumbuh, lalu turun di giliran 7. `bench.py` tidak mencetak panjang transkrip, tetapi
   penurunannya adalah penulisan ulang. Transkrip yang ditulis ulang tidak bisa menjadi prefix.
   Fungsi mana di `loop.py` yang menulis ulangnya, dan seperti apa bentuk "memendekkan konteks tanpa
   menyentuh prefix"?

---

## Petunjuk 3 — bentuk perbaikannya

Empat suntingan. Tidak ada yang di `agent/provider.py`, dan tidak ada yang membuat prompt lebih
pendek.

**1. `tools_for_request()` mengembalikan `TOOLS`.** Definisinya sudah berupa list dengan urutan
tetap. String snapshot tidak menambah apa pun yang dipakai model.

**2. `system_prompt()` tidak menerima jam.** Blok buku panduan menjadi konstan, dan
`build_request()` menandainya sebagai breakpoint pertama dengan masa hidup lebih panjang:

```python
blocks = [Block(role="system", text=system_prompt(), cache=True, ttl=LONG_TTL)]
```

`LONG_TTL` = 3.600 detik. Penulisan cache dengan masa hidup itu lebih mahal per token daripada yang
5 menit, tetapi buku panduan ditulis sekali dan dibaca sepanjang jam itu. Pemeriksaan F adalah
giliran setelah jeda sepuluh menit: dengan TTL bawaan 300 detik, giliran itu tidak menemukan apa pun
dan menulis ulang 6.135 token.

**3. Tanggal ikut bersama gilirannya.** Di `run_ticket()`, cap pesan yang kamu tambahkan, bukan
prompt yang kamu bangun:

```python
history.append({"role": "user", "text": f"{text}\n\n[session date {today(clock)}]"})
```

Ini bedanya memperbaiki cache dengan menghapus fiturnya. Pemeriksaan C menguji dua-duanya.

**4. `compress()` dihapus, atau berubah menjadi pesan yang ditambahkan.** Versi bersihnya:
tambahkan semuanya, jangan pernah menulis ulang. Kalau kamu benar-benar butuh ringkasan, tambahkan
sebagai blok *baru* di ujung — blok lama tetap utuh, jadi prefix masih cocok dan permintaan
berikutnya masih bisa membacanya. Hapus pemanggilan `SUMMARY_KEEP` dan pemeriksaan D jadi hijau;
jumlah tokenmu akan **naik** sekitar 6% dan tagihanmu turun, dan itulah inti seluruh lab ini.

**5. Cetak pengukurannya.** Di `loop.py`:

```python
result = run_all(Provider(clock=Clock()))
print(f"summary turns={result['turns']} hit_rate={result['hit_rate']:.3f} cost_usd={result['cost_usd']:.6f}")
```

Pemeriksaan G menjalankan ulang loop-nya sendiri dan membandingkan angkamu dengan ledger. Angka yang
dicetak tetapi tidak cocok dengan ledger lebih buruk daripada tidak ada angka.
