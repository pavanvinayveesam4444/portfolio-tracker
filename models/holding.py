"""
Holding model — represents stocks currently owned.
One portfolio can have multiple holdings.
"""

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Float, DateTime, ForeignKey
from datetime import datetime, timezone
from models.base import Base


class Holding(Base):
    __tablename__ = "holdings"

    id: Mapped[int] = mapped_column(primary_key=True)
    portfolio_id: Mapped[int] = mapped_column(
        ForeignKey("portfolios.id"),
        nullable=False
    )
    ticker: Mapped[str] = mapped_column(String(10), nullable=False)
    shares: Mapped[float] = mapped_column(Float, nullable=False)
    average_price: Mapped[float] = mapped_column(Float, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )

    portfolio: Mapped["Portfolio"] = relationship(
        "Portfolio",
        back_populates="holdings"
    )
    transactions: Mapped[list["Transaction"]] = relationship(
        "Transaction",
        back_populates="holding",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"Holding(ticker={self.ticker}, shares={self.shares})"