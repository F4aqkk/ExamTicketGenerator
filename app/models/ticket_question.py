from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class TicketQuestion(Base):
    __tablename__ = "ticket_questions"
    ticket_id: Mapped[int] = mapped_column(
        ForeignKey("tickets.id"),
        primary_key=True,
    )
    question_id: Mapped[int] = mapped_column(
        ForeignKey("questions.id"),
        primary_key=True,
    )
    position: Mapped[int] = mapped_column()
