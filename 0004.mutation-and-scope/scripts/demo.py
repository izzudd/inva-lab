#!/usr/bin/env python3
"""Ceritanya. Jalankan dari direktori lab:  make demo

Nggak ada angka yang disembunyikan: semua yang dicetak di sini datang dari
fungsi di `kasir.py` yang sama dengan yang dipakai `make check`.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import kasir  # noqa: E402

# Apa yang seharusnya terjadi: tiap meja memesan satu hal, dan hanya itu.
RENCANA = [
    (1, "kopi", 2),  # meja 1 pesan 2 kopi
    (3, "teh", 1),  # meja 3 pesan 1 teh
    (5, "roti", 1),  # meja 5 pesan 1 roti
]


def rp(n):
    return f"Rp{n:,}".replace(",", ".")


def main():
    print("Tiga meja buka pesanan, satu per satu.\n")

    # Semua meja buka pesanannya dulu...
    pesanan = {meja: kasir.pesanan_baru(meja) for meja, _, _ in RENCANA}
    # ...baru pesanannya diisi.
    for meja, nama, qty in RENCANA:
        kasir.tambah_item(pesanan[meja], nama, qty)

    print("Isi nota tiap meja:")
    for meja, nama, qty in RENCANA:
        isi = ", ".join(f"{i['nama']} x{i['qty']}" for i in pesanan[meja]["item"]) or "(kosong)"
        print(f"  meja {meja}  isi: {isi}")

    print("\nTotal nota tiap meja:")
    for meja, nama, qty in RENCANA:
        print(f"  meja {meja}  total nota: {rp(pesanan[meja]['total'])}")

    print(f"\nKas harian: {rp(kasir.total_kas())}\n")

    # Ringkasan ini dihitung dari data di atas, bukan ditulis tangan.
    masalah = []
    for meja, nama, qty in RENCANA:
        isi = [i["nama"] for i in pesanan[meja]["item"]]
        if isi != [nama]:
            masalah.append(f"nota meja {meja} isinya {isi}, harusnya cuma ['{nama}']")
        if pesanan[meja]["total"] != kasir.MENU[nama] * qty:
            masalah.append(f"total meja {meja} {rp(pesanan[meja]['total'])}, harusnya {rp(kasir.MENU[nama] * qty)}")

    harusnya_kas = sum(kasir.MENU[nama] * qty for _, nama, qty in RENCANA)
    if kasir.total_kas() != harusnya_kas:
        masalah.append(f"kas harian {rp(kasir.total_kas())}, harusnya {rp(harusnya_kas)}")

    if masalah:
        print("Yang barista lihat salah:")
        for baris in masalah:
            print(f"  - {baris}")
    else:
        print("Tiga meja, tiga nota, sesuai pesanannya masing-masing.")


if __name__ == "__main__":
    main()
