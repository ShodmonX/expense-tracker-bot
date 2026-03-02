from datetime import datetime, date as datetime_date
import enum

from sqlalchemy import BigInteger, Float, String, Boolean, Text, Date, DateTime, Enum, Integer
from sqlalchemy.orm import Mapped, mapped_column
from database import Base


def utc_now_naive() -> datetime:
    # PostgreSQL TIMESTAMP WITHOUT TIME ZONE expects offset-naive datetime.
    return datetime.utcnow()


class ExpenseType(enum.Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    YEARLY = "yearly"
    ONCE = "once"


class PaymentFrequency(enum.Enum):
    WEEKLY = "weekly"
    BIWEEKLY = "biweekly"
    MONTHLY = "monthly"
    YEARLY = "yearly"
    QUARTERLY = "quarterly"
    ONCE = "once"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    username: Mapped[str | None] = mapped_column(String(100))
    full_name: Mapped[str | None] = mapped_column(String(200))
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=utc_now_naive
    )


class UserSettings(Base):
    __tablename__ = "user_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    timezone: Mapped[str] = mapped_column(String(64), default="Asia/Tashkent")
    report_format: Mapped[str] = mapped_column(String(8), default="xlsx")
    daily_reminder_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    overdue_reminder_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    daily_summary_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=utc_now_naive,
        onupdate=utc_now_naive,
    )


class Expense(Base):
    __tablename__ = "expenses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(BigInteger, index=True)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    category: Mapped[str | None] = mapped_column(String(100))
    description: Mapped[str | None] = mapped_column(Text)
    date: Mapped[datetime_date] = mapped_column(Date, nullable=False)
    expense_type: Mapped[ExpenseType] = mapped_column(
        Enum(ExpenseType), default=ExpenseType.ONCE
    )
    is_future: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=utc_now_naive
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=utc_now_naive,
        onupdate=utc_now_naive,
    )


class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(BigInteger, index=True)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    category: Mapped[str | None] = mapped_column(String(100))
    description: Mapped[str | None] = mapped_column(Text)
    due_date: Mapped[datetime_date] = mapped_column(Date, nullable=False)
    weekday: Mapped[int | None] = mapped_column(Integer)
    day_of_month: Mapped[int | None] = mapped_column(Integer)
    payment_date: Mapped[datetime_date | None] = mapped_column(Date)
    is_paid: Mapped[bool] = mapped_column(Boolean, default=False)
    is_skipped: Mapped[bool] = mapped_column(Boolean, default=False)
    occurrences_left: Mapped[int | None] = mapped_column(Integer)
    frequency: Mapped[PaymentFrequency] = mapped_column(
        Enum(PaymentFrequency), default=PaymentFrequency.ONCE
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=utc_now_naive
    )
    reminder_sent: Mapped[bool] = mapped_column(Boolean, default=False)
    overdue_last_sent_at: Mapped[datetime | None] = mapped_column(DateTime)


class Income(Base):
    __tablename__ = "income"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(BigInteger, index=True)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    description: Mapped[str] = mapped_column(String(200))
    category: Mapped[str] = mapped_column(String(50), default="Kirim")
    date: Mapped[datetime_date] = mapped_column(Date, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=utc_now_naive
    )
