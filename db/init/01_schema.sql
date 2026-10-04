-- Skema ini sengaja dibuat seperti aplikasi yang sudah jalan di produksi:
-- cuma ada primary key. Nggak ada index tambahan di foreign key.

CREATE TABLE authors (
    id   serial PRIMARY KEY,
    name text NOT NULL
);

CREATE TABLE posts (
    id         serial PRIMARY KEY,
    author_id  integer NOT NULL REFERENCES authors(id),
    title      text NOT NULL,
    body       text NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE comments (
    id          serial PRIMARY KEY,
    post_id     integer NOT NULL REFERENCES posts(id),
    author_name text NOT NULL,
    body        text NOT NULL,
    created_at  timestamptz NOT NULL DEFAULT now()
);
