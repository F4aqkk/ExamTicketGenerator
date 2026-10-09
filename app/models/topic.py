"""Модель темы вопросов."""

from typing import TYPE_CHECKING

from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:  # импорт только для подсказок, при запуске не выполняется
    from app.models.question import Question


class Topic(Base):
    """Тема, к которой относятся вопросы."""

    __tablename__ = "topics"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(unique=True)
    # Вопросы темы. Ленивая загрузка: читаются из базы при первом обращении.
    questions: Mapped[list["Question"]] = relationship(
        back_populates="topic",
    )
