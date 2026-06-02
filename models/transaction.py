"""
Transaction model — records every BUY or SELL action.
One holding can have multiple transactions.
"""

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Float, DateTime, ForeignKey
from datetime import datetime, timezone
from models.base import Base


class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(primary_key=True)
    holding_id: Mapped[int] = mapped_column(
        ForeignKey("holdings.id"),
        nullable=False
    )
    transaction_type: Mapped[str] = mapped_column(
        String(4),
        nullable=False
    )
    shares: Mapped[float] = mapped_column(Float, nullable=False)
    price: Mapped[float] = mapped_column(Float, nullable=False)
    total_value: Mapped[float] = mapped_column(Float, nullable=False)
    transaction_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )

    holding: Mapped["Holding"] = relationship(
        "Holding",
        back_populates="transactions"
    )

    def __repr__(self):
        return f"Transaction(type={self.transaction_type}, shares={self.shares}, price={self.price})"