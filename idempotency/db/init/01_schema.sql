-- Skema ini seperti aplikasi yang sudah jalan di produksi: integritasnya dipegang
-- aplikasi, bukan database. Di luar primary key, tidak ada satu pun UNIQUE
-- constraint di sini.

CREATE TABLE accounts (
    id      serial PRIMARY KEY,
    name    text NOT NULL,
    balance numeric(14, 2) NOT NULL DEFAULT 0
);

CREATE TABLE ledger_entries (
    id          bigserial PRIMARY KEY,
    account_id  integer NOT NULL REFERENCES accounts(id),
    event_id    text NOT NULL,       -- id event dari gateway; stabil untuk event yang sama
    delivery_id text NOT NULL,       -- id tiap pengiriman; berubah tiap kali dikirim ulang
    amount      numeric(14, 2) NOT NULL,
    created_at  timestamptz NOT NULL DEFAULT now()
);
