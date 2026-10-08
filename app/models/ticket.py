"""Модель одного билета."""

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Ticket(Base):
    """Один билет из генерации."""

    __tablename__ = "tickets"
    id: Mapped[int] = mapped_column(primary_key=True)
    generation_id: Mapped[int] = mapped_column(
        ForeignKey("generations.id"),
    )
    # Номер в пачке генерации.
    number: Mapped[int] = mapped_column()
