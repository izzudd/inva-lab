-- Skema lanjutan: jalur webhook sudah lewat lab sebelumnya, jadi idempotensinya
-- sudah ada (tabel processed_events + unique di event_id).
--
-- Yang baru di lab ini: pembayaran yang sama bisa diberitahukan lewat dua jalur.
--   charge_id  -> id pembayaran di sisi gateway. Sama di kedua jalur.
--   event_id   -> id pesan yang memberitahukannya. Beda di tiap jalur.
--   source     -> jalur mana yang mencatat barisnya ("webhook" / "recon").

CREATE TABLE accounts (
    id      serial PRIMARY KEY,
    name    text NOT NULL,
    balance numeric(14, 2) NOT NULL DEFAULT 0
);

CREATE TABLE ledger_entries (
    id          bigserial PRIMARY KEY,
    account_id  integer NOT NULL REFERENCES accounts(id),
    charge_id   text NOT NULL,
    event_id    text NOT NULL,
    delivery_id text NOT NULL,
    source      text NOT NULL,
    amount      numeric(14, 2) NOT NULL,
    created_at  timestamptz NOT NULL DEFAULT now()
);

ALTER TABLE ledger_entries
    ADD CONSTRAINT ledger_entries_event_id_key UNIQUE (event_id);

CREATE TABLE processed_events (
    event_id            text PRIMARY KEY,
    request_fingerprint text NOT NULL,
    response_status     integer NOT NULL DEFAULT 200,
    response_body       jsonb,
    processed_at        timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE reconciliation_runs (
    id          serial PRIMARY KEY,
    run_id      text NOT NULL UNIQUE,
    day         date NOT NULL,
    limit_count integer,
    seen        integer NOT NULL DEFAULT 0,
    inserted    integer NOT NULL DEFAULT 0,
    skipped     integer NOT NULL DEFAULT 0,
    mismatched  jsonb,
    started_at  timestamptz NOT NULL DEFAULT now()
);
