"""Модель одного билета."""

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:  # импорт только для подсказок, при запуске не выполняется
    from app.models.generation import Generation
    from app.models.ticket_question import TicketQuestion


class Ticket(Base):
    """Один билет из генерации."""

    __tablename__ = "tickets"
    # UNIQUE: в одной генерации не может быть двух билетов с одним номером.
    __table_args__ = (
        UniqueConstraint(
            "generation_id",
            "number",
            name="uq_tickets_generation_number",
        ),
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    # CASCADE: удалили генерацию, база сама удаляет её билеты.
    generation_id: Mapped[int] = mapped_column(
        ForeignKey("generations.id", ondelete="CASCADE"),
    )
    # Номер в пачке генерации.
    number: Mapped[int] = mapped_column()
    generation: Mapped["Generation"] = relationship(
        back_populates="tickets",
    )
    # Вопросы билета по порядку. cascade: удалили билет, удаляются
    # и его строки в ticket_questions.
    ticket_questions: Mapped[list["TicketQuestion"]] = relationship(
        back_populates="ticket",
        cascade="all, delete-orphan",
        passive_deletes=True,  # незагруженные строки удалит сама база
        order_by="TicketQuestion.position",
    )
