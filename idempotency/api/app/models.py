from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from .db import Base


class Account(Base):
    __tablename__ = "accounts"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(Text)
    balance: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("0"))


class LedgerEntry(Base):
    __tablename__ = "ledger_entries"

    id: Mapped[int] = mapped_column(primary_key=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("accounts.id"))
    event_id: Mapped[str] = mapped_column(String)
    delivery_id: Mapped[str] = mapped_column(String)
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class DeliveryAttempt(Base):
    """Pengiriman yang pernah datang.

    Tidak lagi dipakai untuk memutuskan idempotensi (itu tugas processed_events),
    tapi tetap dicatat supaya bisa dijawab: "pengiriman ini datang berapa kali?"
    """

    __tablename__ = "delivery_attempts"

    delivery_id: Mapped[str] = mapped_column(String, primary_key=True)
    event_id: Mapped[str] = mapped_column(String)
    processed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ProcessedEvent(Base):
    """Klaim satu event, sekaligus tempat menyimpan jawaban pengiriman pertama.

    Primary key-nya event_id. Itu yang bikin "periksa dulu, baru tulis" tidak
    perlu lagi: database yang memutuskan, di satu statement INSERT.
    """

    __tablename__ = "processed_events"

    event_id: Mapped[str] = mapped_column(String, primary_key=True)
    request_fingerprint: Mapped[str] = mapped_column(String)
    response_status: Mapped[int] = mapped_column(Integer, default=200)
    response_body: Mapped[dict | None] = mapped_column(JSONB)
    processed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
