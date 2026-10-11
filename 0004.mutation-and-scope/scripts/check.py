#!/usr/bin/env python3
"""Target lab ini. Hijau = kamu sudah selesai.

Jalankan dari direktori lab:  make check
Cukup Python 3 standar — nggak butuh Docker, database, atau pip.
"""

import importlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


def rp(n):
    return f"Rp{n:,}".replace(",", ".")


def muat_ulang():
    """Impor kasir.py dari nol, biar tiap pemeriksaan mulai dari keadaan bersih."""
    for nama in list(sys.modules):
        if nama == "kasir":
            del sys.modules[nama]
    return importlib.import_module("kasir")


# ------------------------------------------------------------------ kelompok 1


def kelompok_pesanan():
    """Tiap meja pesanannya sendiri-sendiri."""
    kasir = muat_ulang()

    hasil = []

    # Satu meja pesan; meja lain yang belum pesan apa-apa tetap kosong.
    meja1 = kasir.pesanan_baru(1)
    meja3 = kasir.pesanan_baru(3)
    meja5 = kasir.pesanan_baru(5)
    kasir.tambah_item(meja1, "kopi", 2)

    bocor = [p["meja"] for p in (meja3, meja5) if p["item"]]
    hasil.append(
        (
            "A1 meja yang belum pesan tetap kosong",
            not bocor,
            "rapi" if not bocor else f"ikut keisi: meja {bocor}",
        )
    )

    # Dua meja pesan menu yang beda; tiap nota cuma punya pesanannya sendiri.
    kiri = kasir.pesanan_baru(7)
    kanan = kasir.pesanan_baru(9)
    kasir.tambah_item(kiri, "teh", 1)
    kasir.tambah_item(kanan, "roti", 1)

    isi_kiri = [i["nama"] for i in kiri["item"]]
    isi_kanan = [i["nama"] for i in kanan["item"]]
    rapi = isi_kiri == ["teh"] and isi_kanan == ["roti"]
    hasil.append(
        (
            "A2 tiap nota cuma berisi pesanan meja itu",
            rapi,
            f"meja 7: {isi_kiri}, meja 9: {isi_kanan}",
        )
    )

    return hasil


# ------------------------------------------------------------------ kelompok 2


def kelompok_total():
    """Total nota ikut isi pesanannya."""
    kasir = muat_ulang()

    hasil = []

    pesanan = kasir.pesanan_baru(2)
    kasir.tambah_item(pesanan, "kopi", 2)
    kasir.tambah_item(pesanan, "teh", 1)

    harusnya = 2 * 15000 + 1 * 8000
    hasil.append(
        (
            "B1 total nota sama dengan jumlah itemnya",
            pesanan["total"] == harusnya,
            f"nota {rp(pesanan['total'])}, harusnya {rp(harusnya)}",
        )
    )

    # qty harus ikut dikalikan, bukan cuma dihitung sekali.
    lain = kasir.pesanan_baru(4)
    kasir.tambah_item(lain, "kopi", 3)
    hasil.append(
        (
            "B2 qty dikalikan, bukan ditambah sekali",
            lain["total"] == 3 * 15000,
            f"nota {rp(lain['total'])}, harusnya {rp(3 * 15000)}",
        )
    )

    return hasil


# ------------------------------------------------------------------ kelompok 3


def kelompok_kas():
    """Kas harian nambahnya pas: sebesar yang benar-benar terjual."""
    kasir = muat_ulang()

    awal = kasir.total_kas()

    pesanan = kasir.pesanan_baru(6)
    kasir.tambah_item(pesanan, "roti", 2)  # 24000
    kasir.tambah_item(pesanan, "teh", 1)  # 8000

    naik = kasir.total_kas() - awal
    harusnya = 2 * 12000 + 1 * 8000

    return [
        (
            "C1 kas bertambah sebesar penjualannya",
            naik == harusnya,
            f"kas naik {rp(naik)}, harusnya {rp(harusnya)}",
        ),
        (
            "C2 nota ikut benar walau kas yang dicek",
            pesanan["total"] == harusnya,
            f"nota {rp(pesanan['total'])}",
        ),
    ]


def main():
    print("\ncheck 1 - tiap meja pesanannya sendiri")
    a = kelompok_pesanan()

    print("check 2 - total nota ikut isi pesanannya")
    b = kelompok_total()

    print("check 3 - kas harian bertambah pas")
    c = kelompok_kas()

    print()
    for label, cases in (
        ("1. tiap nota cuma punya isi pesanan meja itu", a),
        ("2. total nota dihitung dari itemnya", b),
        ("3. kas harian bertambah sebesar penjualannya", c),
    ):
        passed = all(ok for _, ok, _ in cases)
        print(f"  [{'LULUS' if passed else 'GAGAL'}] {label}")
        for nama, ok, detail in cases:
            print(f"       [{'v' if ok else 'x'}] {nama} - {detail}")
    print()

    semua = a + b + c
    gagal = [nama for nama, ok, _ in semua if not ok]

    if not gagal:
        print("Target tercapai. Dua hal untuk kamu periksa sendiri:")
        print("  1. `make demo` - ceritanya sudah bersih sekarang.")
        print("  2. tanya ke dirimu: waktu aku nulis `x = ...`, benda mana yang aku ubah?")
        return 0

    print(f"Belum selesai: {len(gagal)} dari {len(semua)} pemeriksaan merah.")
    print("Fokus ke satu kelompok dulu, jangan sekaligus.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
