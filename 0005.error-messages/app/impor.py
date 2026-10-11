#!/usr/bin/env python3
"""impor.py — baca file pendaftar (.csv), laporkan SEMUA baris yang bermasalah.

Satu masalah = satu baris laporan, ke stderr, formatnya:

    baris <nomor di file>: <kolom> — <apa yang salah, nilai jeleknya, dan yang diharapkan>

Dipakai dari direktori lab:

    python3 app/impor.py data/pendaftar.csv

Kode keluar: 0 = bersih, 1 = ada baris bermasalah, 2 = caranya salah (file tidak ada, dll).
"""
import csv
import sys

KOLOM = ("nama", "email", "umur")
UMUR_MIN, UMUR_MAX = 1, 120


def periksa(baris):
    """Daftar (kolom, pesan) untuk satu baris data. Kosong kalau barisnya benar."""
    masalah = []

    if len(baris) != len(KOLOM):
        masalah.append((
            "jumlah kolom",
            f"jumlah kolom tidak cocok: ketemu {len(baris)}, seharusnya {len(KOLOM)} — "
            f"cek pemisah koma di baris ini",
        ))
        return masalah  # kolomnya saja tidak pas, isinya belum bisa dipercaya

    nama, email, umur = (sel.strip() for sel in baris)

    if not nama:
        masalah.append(("nama", "kolom nama kosong, padahal harus diisi"))

    if "@" not in email:
        masalah.append((
            "email",
            f"'{email}' bukan alamat email karena tidak ada tanda '@' — "
            f"contoh yang benar: pendaftar@contoh.com",
        ))

    try:
        umur_angka = int(umur)
    except ValueError:
        masalah.append((
            "umur",
            f"'{umur}' bukan angka — isi dengan bilangan bulat, misalnya 25",
        ))
    else:
        if not (UMUR_MIN <= umur_angka <= UMUR_MAX):
            masalah.append((
                "umur",
                f"{umur_angka} di luar rentang {UMUR_MIN}-{UMUR_MAX} — "
                f"isi umur antara {UMUR_MIN} dan {UMUR_MAX}",
            ))

    return masalah


def main(argv):
    if len(argv) != 2:
        sys.stderr.write("cara pakai: python3 app/impor.py <file.csv>\n")
        return 2

    path = argv[1]
    try:
        berkas = open(path, newline="", encoding="utf-8")
    except FileNotFoundError:
        sys.stderr.write(f"file '{path}' tidak ada — cek nama dan lokasinya\n")
        return 2
    except IsADirectoryError:
        sys.stderr.write(f"'{path}' itu folder, bukan file — tunjuk file .csv-nya\n")
        return 2

    jumlah = 0
    with berkas:
        pembaca = csv.reader(berkas)
        try:
            next(pembaca)  # baris judul, bukan data
        except StopIteration:
            sys.stderr.write(f"file '{path}' kosong, tidak ada baris judul\n")
            return 1

        # start=2: baris pertama data ada di baris 2 file (baris 1 = judul).
        for nomor, baris in enumerate(pembaca, start=2):
            for kolom, pesan in periksa(baris):
                sys.stderr.write(f"baris {nomor}: {kolom} — {pesan}\n")
                jumlah += 1

    if jumlah:
        sys.stderr.write(f"\n{jumlah} masalah ditemukan, tidak ada baris yang diimpor.\n")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
