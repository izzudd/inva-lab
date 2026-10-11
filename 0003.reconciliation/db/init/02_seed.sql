-- Data "produksi" yang kecil: tiga akun, dua di antaranya sudah punya riwayat
-- dari hari-hari sebelumnya (semuanya lewat webhook).

INSERT INTO accounts (id, name, balance) VALUES
    (1, 'Toko Kopi Rame', 150000.00),
    (2, 'Warung Bu Sri', 75000.00),
    (3, 'Katering Amanah', 0);

SELECT setval('accounts_id_seq', 3);

INSERT INTO ledger_entries (account_id, charge_id, event_id, delivery_id, source, amount) VALUES
    (1, 'ch_seed_0001', 'evt_seed_0001', 'dlv_seed_0001', 'webhook', 150000.00),
    (2, 'ch_seed_0002', 'evt_seed_0002', 'dlv_seed_0002', 'webhook', 75000.00);
