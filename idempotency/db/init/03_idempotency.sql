-- Lab 2 - jawaban, bagian database.
--
-- Keputusan "sudah pernah diproses atau belum" harus dipegang database, bukan
-- aplikasi. Tiga hal yang dipasang di sini:
--
--   1. ledger_entries.event_id  -> satu event cuma boleh punya satu baris ledger
--   2. processed_events         -> satu event cuma boleh diproses satu kali, dan
--                                  yang memutuskan itu operasi INSERT-nya sendiri
--   3. processed_events.response_*  -> jawaban pengiriman pertama disimpan, supaya
--                                  pengiriman ulang bisa dijawab dengan jawaban
--                                  yang sama (bukan dengan error "sudah diproses")

-- Di database produksi yang sudah kena masalah ini, perintah di bawah akan gagal:
--
--   ERROR: could not create unique index "ledger_entries_event_id_key"
--   DETAIL:  Key (event_id)=(evt_...) is duplicated.
--
-- Itu bukan alasan untuk membatalkan pemasangannya - artinya kamu harus
-- membersihkan duplikatnya lebih dulu (dan memutuskan mana yang benar), baru
-- memasang unique-nya. Di tabel besar, buat index-nya dengan
-- CREATE UNIQUE INDEX CONCURRENTLY supaya tabelnya tidak terkunci saat dibangun.
ALTER TABLE ledger_entries
    ADD CONSTRAINT ledger_entries_event_id_key UNIQUE (event_id);

CREATE TABLE processed_events (
    event_id            text PRIMARY KEY,
    request_fingerprint text NOT NULL,
    response_status     integer NOT NULL DEFAULT 200,
    response_body       jsonb,
    processed_at        timestamptz NOT NULL DEFAULT now()
);
