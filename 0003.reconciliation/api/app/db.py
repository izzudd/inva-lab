import os

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

DATABASE_URL = os.environ.get(
    "DATABASE_URL", "postgresql+psycopg2://inva:inva@db:5432/inva"
)

# Pool-nya sengaja lega: webhook datang beberapa sekaligus, dan endpoint di sini
# sync (dilayani threadpool), jadi satu request = satu koneksi.
engine = create_engine(
    DATABASE_URL,
    pool_size=30,
    max_overflow=10,
    pool_pre_ping=True,
    future=True,
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


class Base(DeclarativeBase):
    pass
