"""Модель критериев генерации."""

from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Generation(Base):
    """Один запуск генерации билетов."""

    __tablename__ = "generations"
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column()
    created_at: Mapped[str] = mapped_column()
    tickets_count: Mapped[int] = mapped_column()
    questions_per_ticket: Mapped[int] = mapped_column()
