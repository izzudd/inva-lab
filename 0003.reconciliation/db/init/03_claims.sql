-- Lab 3 - jawaban, bagian database.
--
-- Kuncinya pindah dari pesan ke pembayaran:
--
--   sebelum: processed_events(event_id PK)          satu kejadian satu klaim
--   sesudah: payment_claims(charge_id PK)           satu pembayaran satu klaim
--
-- Akibatnya di ledger:
--
--   ledger_entries.event_id  -> tidak unik lagi. Dua pesan berbeda boleh
--                               memberitahukan pembayaran yang sama.
--   ledger_entries.charge_id -> yang unik, karena satu pembayaran cuma boleh
--                               punya satu baris di ledger.
--
-- Di database produksi, urutannya begini: bereskan dulu duplikat yang sudah
-- ada (dan putuskan mana yang benar - itu keputusan bisnis, bukan keputusan
-- SQL), baru pasang unique-nya. Kalau langsung dipasang, ALTER TABLE-nya gagal
-- dengan "Key (charge_id)=(...) is duplicated".

DROP TABLE processed_events;

CREATE TABLE payment_claims (
    charge_id           text PRIMARY KEY,
    first_seen_from     text NOT NULL,   -- 'webhook' atau 'recon'
    first_message_id    text,            -- id pesan pertama (event_id webhook, atau run_id job)
    request_fingerprint text NOT NULL,
    response_status     integer NOT NULL DEFAULT 200,
    response_body       jsonb,
    recorded_amount     numeric(14, 2),
    claimed_at          timestamptz NOT NULL DEFAULT now()
);

ALTER TABLE ledger_entries DROP CONSTRAINT ledger_entries_event_id_key;
ALTER TABLE ledger_entries ADD CONSTRAINT ledger_entries_charge_id_key UNIQUE (charge_id);
