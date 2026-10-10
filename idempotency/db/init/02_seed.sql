-- Data "produksi" yang kecil: tiga akun, dua di antaranya sudah punya riwayat.

INSERT INTO accounts (id, name, balance) VALUES
    (1, 'Toko Kopi Rame', 150000.00),
    (2, 'Warung Bu Sri', 75000.00),
    (3, 'Katering Amanah', 0);

SELECT setval('accounts_id_seq', 3);

INSERT INTO ledger_entries (account_id, event_id, delivery_id, amount) VALUES
    (1, 'evt_seed_01', 'dlv_seed_01', 150000.00),
    (2, 'evt_seed_02', 'dlv_seed_02', 75000.00);
