"""Модель вопроса в билете."""

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:  # импорт только для подсказок, при запуске не выполняется
    from app.models.question import Question
    from app.models.ticket import Ticket


class TicketQuestion(Base):
    """Связь билета с вопросом и порядок вопроса в билете."""

    __tablename__ = "ticket_questions"
    # CASCADE: удалили билет, удаляются и его вопросы билета.
    ticket_id: Mapped[int] = mapped_column(
        ForeignKey("tickets.id", ondelete="CASCADE"),
        primary_key=True,
    )
    # RESTRICT: вопрос, который стоит в сохранённом билете, удалить нельзя.
    question_id: Mapped[int] = mapped_column(
        ForeignKey("questions.id", ondelete="RESTRICT"),
        primary_key=True,
    )
    # Номер вопроса в билете.
    position: Mapped[int] = mapped_column()
    ticket: Mapped["Ticket"] = relationship(
        back_populates="ticket_questions",
    )
    # Сам вопрос. Читается из базы при первом обращении.
    question: Mapped["Question"] = relationship()
