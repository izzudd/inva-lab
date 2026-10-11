#!/usr/bin/env python3
"""check.py — garis akhir lab 0005.error-messages.

Menjalankan `app/impor.py` pada beberapa file contoh, lalu memeriksa laporan
yang keluar. Mesin yang menilai; kamu yang membuatnya hijau.

    python3 scripts/check.py
"""
import re
import subprocess
import sys
from pathlib import Path

LAB = Path(__file__).resolve().parent.parent
IMPOR = LAB / "app" / "impor.py"
FILE_HILANG = "data/contoh/tidak-ada.csv"

# Satu baris laporan dianggap "baris masalah" kalau memuat kata "baris" + angka.
POLA_BARIS = re.compile(r"baris\s+(\d+)")
KOLOM_DIKENAL = ("jumlah kolom", "nama", "email", "umur")

# Fixture -> daftar masalah yang SEHARUSNYA dilaporkan.
# Tiap masalah: (nomor baris fisik di file, kolom, nilai jelek, kata kunci harapan).
HARAPAN = {
    "data/pendaftar.csv": [],
    "data/contoh/kosong.csv": [
        (2, "nama", None, ("kosong",)),
    ],
    "data/contoh/beberapa.csv": [
        (3, "nama", None, ("kosong",)),
        (3, "email", "budi.example.com", ("@",)),
        (4, "umur", "dua puluh", ("angka",)),
        (5, "umur", "200", ("120",)),
    ],
    "data/contoh/kolom.csv": [
        (2, "jumlah kolom", "2", ("3",)),
        (3, "jumlah kolom", "4", ("3",)),
    ],
}


def jalankan(path):
    hasil = subprocess.run(
        [sys.executable, str(IMPOR), path],
        cwd=str(LAB),
        capture_output=True,
        text=True,
    )
    return hasil.returncode, hasil.stdout + hasil.stderr


def baris_masalah(teks):
    """(nomor, kolom, isi baris) untuk tiap baris yang tampak seperti laporan masalah."""
    hasil = []
    for baris in teks.splitlines():
        m = POLA_BARIS.search(baris)
        if not m:
            continue
        kolom = next((k for k in KOLOM_DIKENAL if k in baris), None)
        hasil.append((int(m.group(1)), kolom, baris))
    return hasil


def main():
    rc = {}
    keluaran = {}
    masalah = {}
    for path in HARAPAN:
        kode, teks = jalankan(path)
        rc[path] = kode
        keluaran[path] = teks
        masalah[path] = baris_masalah(teks)

    rc_hilang, teks_hilang = jalankan(FILE_HILANG)

    hasil = []

    # A — file bersih: tanpa masalah, kode keluar 0.
    a = rc["data/pendaftar.csv"] == 0 and not masalah["data/pendaftar.csv"]
    hasil.append(("A", "file bersih tidak menghasilkan satu pun masalah", a,
                  f"keluar={rc['data/pendaftar.csv']}, "
                  f"{len(masalah['data/pendaftar.csv'])} masalah"))

    # B — tidak ada traceback Python yang bocor ke pengguna.
    semua_teks = list(keluaran.values()) + [teks_hilang]
    ada_traceback = any("Traceback (most recent call last)" in t for t in semua_teks)
    hasil.append(("B", "tidak ada traceback yang bocor ke layar pengguna", not ada_traceback,
                  "ada traceback" if ada_traceback else "bersih"))

    # C — semua masalah dilaporkan, bukan berhenti di yang pertama.
    dilapor = len(masalah["data/contoh/beberapa.csv"])
    c = dilapor == len(HARAPAN["data/contoh/beberapa.csv"])
    hasil.append(("C", "semua masalah dilaporkan, bukan berhenti di yang pertama", c,
                  f"{dilapor} dari {len(HARAPAN['data/contoh/beberapa.csv'])} masalah"))

    # D — nomor baris yang dilaporkan = nomor baris di file (bukan index data).
    set_beberapa = {(n, k) for n, k, _ in masalah["data/contoh/beberapa.csv"]}
    harap_beberapa = {(n, k) for n, k, _, _ in HARAPAN["data/contoh/beberapa.csv"]}
    d = set_beberapa == harap_beberapa
    hasil.append(("D", "nomor baris cocok dengan nomor baris di file", d,
                  f"dilapor={sorted(set_beberapa)} harap={sorted(harap_beberapa)}"))

    # E — tiap masalah menyebut kolom yang salah, di semua fixture.
    e = True
    for path, harap in HARAPAN.items():
        set_dilapor = {(n, k) for n, k, _ in masalah[path]}
        set_harap = {(n, k) for n, k, _, _ in harap}
        if set_dilapor != set_harap:
            e = False
    hasil.append(("E", "tiap masalah menyebut kolom yang salah", e,
                  "kolom" if e else "ada baris tanpa kolom yang benar"))

    # F — tiap masalah mengutip nilai jeleknya dan menyebut yang diharapkan.
    f = True
    kurang = []
    for path, harap in HARAPAN.items():
        daftar = masalah[path]
        for nomor, kolom, nilai, kata in harap:
            cocok = next((isi for n, k, isi in daftar
                          if n == nomor and k == kolom), None)
            if cocok is None:
                f = False
                kurang.append(f"baris {nomor} {kolom}")
                continue
            if nilai is not None and nilai not in cocok:
                f = False
                kurang.append(f"nilai {nilai!r} tidak disebut")
            if not any(k in cocok for k in kata):
                f = False
                kurang.append(f"harapan {kata} tidak disebut")
    hasil.append(("F", "tiap masalah menyebut nilai jelek + apa yang diharapkan", f,
                  "lengkap" if f else "; ".join(kurang[:3])))

    # G — kode keluar membedakan tiga keadaan.
    g = (rc["data/pendaftar.csv"] == 0
         and rc["data/contoh/kosong.csv"] == 1
         and rc_hilang == 2)
    hasil.append(("G", "kode keluar beda: 0 bersih, 1 ada masalah, 2 dipakai salah", g,
                  f"bersih={rc['data/pendaftar.csv']} "
                  f"masalah={rc['data/contoh/kosong.csv']} "
                  f"file-hilang={rc_hilang}"))

    print()
    for tag, judul, ok, detail in hasil:
        tanda = "HIJAU" if ok else "MERAH"
        print(f"  [{tanda}] {tag}. {judul}  ({detail})")
    print()

    hijau = sum(1 for _, _, ok, _ in hasil if ok)
    total = len(hasil)
    if hijau == total:
        print(f"check: {hijau}/{total} hijau — selesai")
        return 0
    print(f"check: {hijau}/{total} hijau — lab belum selesai")
    return 1


if __name__ == "__main__":
    sys.exit(main())
