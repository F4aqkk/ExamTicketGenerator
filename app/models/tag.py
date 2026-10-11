"""Метка вопроса (тег)."""

from typing import TYPE_CHECKING

from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:  # импорт только для подсказок, при запуске не выполняется
    from app.models.question import Question


class Tag(Base):
    """Тег"""

    __tablename__ = "tags"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(unique=True)
    # Вопросы с этим тегом (через таблицу question_tags).
    questions: Mapped[list["Question"]] = relationship(
        secondary="question_tags",
        back_populates="tags",
    )
