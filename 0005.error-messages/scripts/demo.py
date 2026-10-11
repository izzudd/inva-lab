#!/usr/bin/env python3
"""demo.py — jalankan importer pada file-file contoh, lihat apa yang dilihat pengguna.

    python3 scripts/demo.py
"""
import subprocess
import sys
from pathlib import Path

LAB = Path(__file__).resolve().parent.parent
IMPOR = LAB / "app" / "impor.py"

FILE = [
    ("data/pendaftar.csv", "file bersih, empat pendaftar yang semuanya benar"),
    ("data/contoh/kosong.csv", "satu baris tanpa nama"),
    ("data/contoh/beberapa.csv", "beberapa baris bermasalah sekaligus"),
    ("data/contoh/kolom.csv", "ada baris dengan jumlah kolom yang salah"),
    ("data/contoh/tidak-ada.csv", "file yang salah ketik namanya"),
]


def main():
    print("Lab 0005.error-messages — yang dilihat pengguna\n")
    for path, cerita in FILE:
        hasil = subprocess.run(
            [sys.executable, str(IMPOR), path],
            cwd=str(LAB), capture_output=True, text=True,
        )
        print("=" * 72)
        print(f"$ python3 app/impor.py {path}")
        print(f"  # {cerita}")
        print("-" * 72)
        keluaran = (hasil.stdout + hasil.stderr).rstrip("\n")
        print(keluaran if keluaran else "(tidak ada keluaran)")
        print(f"-> kode keluar: {hasil.returncode}")
        print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
