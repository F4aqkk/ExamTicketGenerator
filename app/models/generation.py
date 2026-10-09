"""Модель критериев генерации."""

from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:  # импорт только для подсказок, при запуске не выполняется
    from app.models.ticket import Ticket


class Generation(Base):
    """Один запуск генерации билетов."""

    __tablename__ = "generations"
    # CHECK: количество билетов и вопросов в билете больше нуля.
    __table_args__ = (
        CheckConstraint(
            "tickets_count > 0",
            name="ck_generations_tickets_count",
        ),
        CheckConstraint(
            "questions_per_ticket > 0",
            name="ck_generations_questions_per_ticket",
        ),
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column()
    # DEFAULT: если дату не передали, база сама ставит текущее время.
    created_at: Mapped[str] = mapped_column(
        server_default=func.current_timestamp(),
    )
    tickets_count: Mapped[int] = mapped_column()
    questions_per_ticket: Mapped[int] = mapped_column()
    # Билеты генерации по порядку номеров. cascade: удалили генерацию,
    # вместе с ней удаляются и её билеты.
    tickets: Mapped[list["Ticket"]] = relationship(
        back_populates="generation",
        cascade="all, delete-orphan",
        order_by="Ticket.number",
    )
