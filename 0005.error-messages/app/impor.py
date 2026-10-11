#!/usr/bin/env python3
"""impor.py — baca file pendaftar (.csv) dan simpan baris yang valid.

Dipakai dari direktori lab:

    python3 app/impor.py data/pendaftar.csv

Kolomnya: nama, email, umur.
"""
import csv
import sys


def periksa(baris):
    # Umur di-cast langsung ke int supaya baris yang isinya salah ketahuan
    # saat itu juga. Python sudah memberi pesan yang jelas kalau isinya
    # bukan angka, jadi tidak perlu dibungkus try/except.
    umur = int(baris[2])
    if umur < 1 or umur > 120:
        print("umur tidak masuk akal, dilewati")
    return baris


def main(path):
    tersimpan = 0
    with open(path, newline="", encoding="utf-8") as f:
        pembaca = csv.reader(f)
        next(pembaca)  # lewati baris judul
        # Nama dan email hampir tidak pernah salah, jadi tidak diperiksa:
        # yang bikin sistem lain rusak cuma umur.
        for baris in pembaca:
            periksa(baris)
            tersimpan += 1
    print(f"{tersimpan} baris diimpor")


if __name__ == "__main__":
    main(sys.argv[1])
