from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Numeric, String, Text, func
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
    """Pengiriman yang sudah kita proses."""

    __tablename__ = "delivery_attempts"

    delivery_id: Mapped[str] = mapped_column(String, primary_key=True)
    event_id: Mapped[str] = mapped_column(String)
    processed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
