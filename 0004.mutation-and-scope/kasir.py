"""kasir.py — inti aplikasi kiosk kafe. (branch: solusi)

Tiga perbaikan, satu tema: **mana yang kamu ubah, dan benda apa itu sebenarnya.**
"""

MENU = {
    "kopi": 15000,
    "teh": 8000,
    "roti": 12000,
}

TOTAL_KAS = 0


def pesanan_baru(meja, item=None):
    """Buat satu pesanan baru untuk sebuah meja.

    `None` sebagai default, bukan `[]`. Nilai default sebuah fungsi dihitung
    **sekali** waktu fungsinya didefinisikan, lalu dipakai ulang di setiap
    pemanggilan — jadi `item=[]` bukan "list baru tiap panggil", tapi "satu list
    yang sama selamanya". List itu baru dibuat di dalam fungsi, tepat saat
    pesanannya benar-benar dibuat.
    """
    if item is None:
        item = []
    return {"meja": meja, "item": item, "total": 0}


def tambah_item(pesanan, nama, qty=1):
    """Tambahkan satu item ke pesanan, lalu hitung ulang totalnya."""
    harga = MENU[nama]
    pesanan["item"].append({"nama": nama, "qty": qty, "harga": harga})

    # `total` di sini cuma nama lokal. Kalau kita cuma menambah ke nama lokal,
    # yang berubah cuma lokalnya; `pesanan` tidak pernah tahu. Yang harus diubah
    # adalah nilai DI DALAM dict-nya.
    pesanan["total"] = pesanan["total"] + harga * qty

    catat_penjualan(harga * qty)
    return pesanan


def catat_penjualan(jumlah):
    """Tambah pemasukan ke kas harian.

    `TOTAL_KAS` tinggal di scope modul, bukan di scope fungsi. Menugaskan ke
    nama itu dari dalam fungsi tanpa `global` bikin Python mengira kita sedang
    bikin variabel lokal baru — dan kalau ditulis `TOTAL_KAS = TOTAL_KAS + x`,
    malah `UnboundLocalError`. `global` bilang: yang aku maksud nama di luar,
    bukan nama baru di sini.
    """
    global TOTAL_KAS
    TOTAL_KAS = TOTAL_KAS + jumlah
    return TOTAL_KAS


def total_kas():
    """Berapa pemasukan kas hari ini."""
    return TOTAL_KAS
