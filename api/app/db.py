import os
import threading

from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, sessionmaker

DATABASE_URL = os.environ.get(
    "DATABASE_URL", "postgresql+psycopg2://inva:inva@db:5432/inva"
)

engine = create_engine(
    DATABASE_URL,
    pool_size=10,
    max_overflow=5,
    pool_pre_ping=True,
    future=True,
)


class QueryCounter(threading.local):
    """Menghitung query per-thread.

    Setiap request di FastAPI (endpoint sync) dilayani utuh oleh satu thread,
    jadi penghitung ini akurat untuk satu request selama tidak ada request lain
    di thread yang sama pada saat bersamaan.
    """

    def __init__(self) -> None:
        self.value = 0

    def reset(self) -> None:
        self.value = 0


query_counter = QueryCounter()


@event.listens_for(engine, "before_cursor_execute")
def _count_query(conn, cursor, statement, parameters, context, executemany):
    query_counter.value += 1


SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


class Base(DeclarativeBase):
    pass
