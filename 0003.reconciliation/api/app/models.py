from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Date, DateTime, ForeignKey, Integer, Numeric, String, Text, func
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
    charge_id: Mapped[str] = mapped_column(String)      # id pembayaran di sisi gateway
    event_id: Mapped[str] = mapped_column(String)       # id pesan/kejadian yang memberitahukannya
    delivery_id: Mapped[str] = mapped_column(String)    # id pengiriman pesan itu
    source: Mapped[str] = mapped_column(String)         # "webhook" atau "recon"
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ProcessedEvent(Base):
    """Klaim sebuah kejadian: satu event_id cuma boleh ditulis satu kali.

    Namanya sisa dari waktu cuma ada jalur webhook. Sekarang jalur rekonsiliasi
    juga menulis klaimnya di sini (lihat ledger.py).
    """

    __tablename__ = "processed_events"

    event_id: Mapped[str] = mapped_column(String, primary_key=True)
    request_fingerprint: Mapped[str] = mapped_column(String)
    response_status: Mapped[int] = mapped_column(Integer, default=200)
    response_body: Mapped[dict | None] = mapped_column(JSONB)
    processed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ReconciliationRun(Base):
    __tablename__ = "reconciliation_runs"

    id: Mapped[int] = mapped_column(primary_key=True)
    run_id: Mapped[str] = mapped_column(String, unique=True)
    day: Mapped[date] = mapped_column(Date)
    limit_count: Mapped[int | None] = mapped_column(Integer)
    seen: Mapped[int] = mapped_column(Integer, default=0)
    inserted: Mapped[int] = mapped_column(Integer, default=0)
    skipped: Mapped[int] = mapped_column(Integer, default=0)
    mismatched: Mapped[list | None] = mapped_column(JSONB)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
