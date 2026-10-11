"""kasir.py — inti aplikasi kiosk kafe.

Ini file yang kamu kerjakan. Boleh diubah sesukamu, asal tiga fungsi publik
(`pesanan_baru`, `tambah_item`, `total_kas`) tetap bisa dipanggil dengan cara
yang sama seperti di README — `make check` memanggil ketiganya.

Nggak ada database, nggak ada Docker: semuanya Python standar, cukup Python 3.
"""

# Daftar menu dan harganya (rupiah). Jangan diubah.
MENU = {
    "kopi": 15000,
    "teh": 8000,
    "roti": 12000,
}

# Pemasukan kas hari ini, dalam rupiah.
TOTAL_KAS = 0


def pesanan_baru(meja, item=[]):
    """Buat satu pesanan baru untuk sebuah meja.

    `meja` cuma nomor meja. Pesanannya mulai kosong, lalu diisi lewat
    `tambah_item`.
    """
    return {"meja": meja, "item": item, "total": 0}


def tambah_item(pesanan, nama, qty=1):
    """Tambahkan satu item ke pesanan, lalu hitung ulang totalnya."""
    harga = MENU[nama]
    pesanan["item"].append({"nama": nama, "qty": qty, "harga": harga})

    # Hitung total pesanan dari item yang sudah masuk.
    total = pesanan["total"]
    total = total + harga * qty

    # Sekalian catat pemasukannya ke kas.
    catat_penjualan(harga * qty)
    return pesanan


def catat_penjualan(jumlah):
    """Tambah pemasukan ke kas harian.

    Dipisah dari `tambah_item` biar gampang dipakai ulang.
    """
    total = TOTAL_KAS
    total = total + jumlah
    return total


def total_kas():
    """Berapa pemasukan kas hari ini."""
    return TOTAL_KAS
