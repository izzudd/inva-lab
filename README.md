# inva-lab

Lab praktik untuk [invasikode.com](https://invasikode.com) — belajar dengan cara mentok dulu,
bukan dengan cara membaca *happy path*.

Tiap lab adalah repo kecil yang **jalan**, sengaja dibuat lambat atau salah dengan cara yang
realistis, dan punya garis akhir yang bisa diperiksa mesin. Tugasmu bukan membaca, tapi bikin
`make check` hijau.

## Daftar lab

Direktori diberi prefix angka supaya urutannya kelihatan langsung di repo: kerjakan dari yang
paling awal, karena tiap lab menganggap kamu sudah melewati lab sebelumnya.

| Lab | Topik | Bentuk masalahnya |
|---|---|---|
| [`0001.n-plus-one/`](0001.n-plus-one/) | N+1 query, index yang hilang | endpoint feed: 41 query, 1,1 detik |
| [`0002.idempotency/`](0002.idempotency/) | Idempotensi, unique key, lost update | webhook: 1 event dikirim 4× jadi 4 baris ledger |
| [`0003.reconciliation/`](0003.reconciliation/) | Satu fakta dari dua jalur, job yang boleh diulang | webhook + job rekonsiliasi: 6 pembayaran jadi 12 baris ledger |

## Cara pakai

```bash
git clone https://github.com/izzudd/inva-lab.git
cd inva-lab/0001.n-plus-one     # atau direktori lab mana pun
make up      # nyalain database + API, seed data
make bench   # lihat angkanya dulu sebelum mengubah apa pun
make check   # target yang harus kamu capai
```

Butuh Docker. Nggak perlu install Python, Node, atau Postgres di mesinmu — semuanya jalan di
dalam container. Port yang dipakai: `58000`/`55432` (lab `0001.n-plus-one`), `58100`/`55433`
(lab `0002.idempotency`), `58102`/`58103`/`55434` (lab `0003.reconciliation`).

Urutan yang disarankan: `0001.n-plus-one`, lalu `0002.idempotency`, lalu `0003.reconciliation` —
lab terakhir menganggap kamu sudah menyelesaikan lab idempotensi, karena kode awalnya memang hasil
dari lab itu.

Nama direktori boleh berubah; nama project Docker-nya dikunci di tiap `docker-compose.yml`
(`name:`), jadi container dan volume-mu nggak ikut berubah kalau foldernya di-rename.

## Jawabannya di mana

Semua jawaban ada di branch **`solusi`**, dipisah per direktori lab. Jangan dibuka sebelum
kamu mentok — kalau kamu cuma membacanya, kamu dapat ilmunya sama seperti membaca tutorial
biasa, dan itu justru yang pengin kita hindari.

```bash
git diff main solusi -- 0001.n-plus-one/
```

Tiap lab juga punya `HINTS.md` dengan tiga tingkat petunjuk. Pakai itu dulu.

## Aturan mainnya

- **Angka di README tiap lab adalah hasil pengukuran, bukan perkiraan.** Kalau kamu mengubah
  sesuatu di dalam lab dan angkanya jadi beda, itu karena mesinmu beda — laporkan lewat issue.
- **Jangan ubah dataset jadi lebih kecil** supaya targetnya gampang. Dataset itu titik soalnya.
- Kalau kamu nyerah, tulis di mana kamu nyerah. Itu bagian dari latihannya.

## Lisensi

MIT — pakai, ubah, dan sebarkan sesukamu.
