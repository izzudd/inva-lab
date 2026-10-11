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
    event_id: Mapped[str] = mapped_column(String)       # id pesan yang memberitahukannya
    delivery_id: Mapped[str] = mapped_column(String)    # id pengiriman pesan itu
    source: Mapped[str] = mapped_column(String)         # "webhook" atau "recon"
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class PaymentClaim(Base):
    """Klaim satu pembayaran - bukan satu pesan.

    Primary key-nya charge_id, karena yang harus terjadi sekali itu pembayarannya,
    bukan pesannya. Dua jalur berbeda sedang membicarakan pembayaran yang sama,
    jadi keduanya harus berdebat di baris yang sama ini.
    """

    __tablename__ = "payment_claims"

    charge_id: Mapped[str] = mapped_column(String, primary_key=True)
    first_seen_from: Mapped[str] = mapped_column(String)
    first_message_id: Mapped[str | None] = mapped_column(String)
    request_fingerprint: Mapped[str] = mapped_column(String)
    response_status: Mapped[int] = mapped_column(Integer, default=200)
    response_body: Mapped[dict | None] = mapped_column(JSONB)
    recorded_amount: Mapped[Decimal | None] = mapped_column(Numeric(14, 2))
    claimed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


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
