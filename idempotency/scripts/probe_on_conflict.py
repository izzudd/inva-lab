"""Uji perilaku ON CONFLICT DO NOTHING saat barisnya masih dipegang transaksi lain.

Pertanyaan yang dijawab: kalau transaksi A menyisipkan baris dan belum commit,
apakah INSERT ... ON CONFLICT DO NOTHING dari transaksi B menunggu A, atau
langsung menjawab "tidak ada baris yang dimasukkan"? Dan kalau A akhirnya
rollback, apakah B jadi menyisipkan barisnya?

Jalankan dari direktori lab (branch `solusi`), API harus sudah jalan:

    docker compose cp scripts/probe_on_conflict.py api:/tmp/probe.py
    docker compose exec api python3 /tmp/probe.py

Hasil di mesin penulis lab (Docker, Postgres 16-alpine):

    A: menyisipkan 'x', belum commit
    B: menyelesaikan INSERT setelah 1,5 detik? belum - B sedang menunggu
    A: rollback
    B: selesai setelah 1.50 detik, baris yang dimasukkan = 1
    isi tabel setelah semuanya selesai: 1 baris

Artinya: DO NOTHING menunggu, dan kalau yang dipegang ternyata batal, penyisipnya
tetap menyisipkan barisnya. Tidak ada klaim yang hilang.
"""
import threading
import time

import psycopg2

DSN = "postgresql://inva:inva@db:5432/inva"


def conn():
    c = psycopg2.connect(DSN)
    c.autocommit = False
    return c


a, b = conn(), conn()
ca, cb = a.cursor(), b.cursor()
ca.execute("DROP TABLE IF EXISTS probe_conf")
ca.execute("CREATE TABLE probe_conf (id text PRIMARY KEY)")
a.commit()

ca.execute("INSERT INTO probe_conf (id) VALUES ('x')")
print("A: menyisipkan 'x', belum commit")

outcome = {}


def run_b():
    started = time.perf_counter()
    cb.execute(
        "INSERT INTO probe_conf (id) VALUES ('x') "
        "ON CONFLICT (id) DO NOTHING RETURNING id"
    )
    rows = cb.fetchall()
    outcome["elapsed"] = time.perf_counter() - started
    outcome["rows"] = len(rows)
    b.commit()


t = threading.Thread(target=run_b)
t.start()
t.join(timeout=1.5)
print(f"B: selesai dalam 1,5 detik? {'ya' if not t.is_alive() else 'belum - B sedang menunggu'}")

if t.is_alive():
    print("A: rollback")
    a.rollback()
    t.join(timeout=10)

print(f"B: selesai setelah {outcome.get('elapsed', -1):.2f} detik, baris yang dimasukkan = {outcome.get('rows')}")

cb.execute("SELECT count(*) FROM probe_conf")
print("isi tabel setelah semuanya selesai:", cb.fetchone()[0], "baris")
a.close()
b.close()
