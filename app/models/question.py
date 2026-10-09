"""Модель вопроса (сложность, тип задания, тема, дата создания)."""

from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:  # импорт только для подсказок, при запуске не выполняется
    from app.models.tag import Tag
    from app.models.topic import Topic


class Question(Base):
    """Вопрос из банка."""

    __tablename__ = "questions"
    # CHECK: база не даст сохранить сложность меньше 1 или больше 3.
    __table_args__ = (
        CheckConstraint(
            "difficulty BETWEEN 1 AND 3",
            name="ck_questions_difficulty",
        ),
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    text: Mapped[str] = mapped_column()
    answer: Mapped[str] = mapped_column()
    difficulty: Mapped[int] = mapped_column()
    task_type: Mapped[str] = mapped_column()
    topic_id: Mapped[int] = mapped_column(ForeignKey("topics.id"))
    # DEFAULT: если дату не передали, база сама ставит текущее время.
    created_at: Mapped[str] = mapped_column(
        server_default=func.current_timestamp(),
    )
    # Связи: тема вопроса и теги вопроса (через таблицу question_tags).
    topic: Mapped["Topic"] = relationship(back_populates="questions")
    tags: Mapped[list["Tag"]] = relationship(
        secondary="question_tags",
        back_populates="questions",
    )
