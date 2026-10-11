"""Модель связки вопроса и тега."""

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class QuestionTag(Base):
    """Связь вопроса с меткой."""

    __tablename__ = "question_tags"
    # CASCADE: удалили вопрос или тег, удаляется и эта связь.
    question_id: Mapped[int] = mapped_column(
        ForeignKey("questions.id", ondelete="CASCADE"),
        primary_key=True,
    )
    tag_id: Mapped[int] = mapped_column(
        ForeignKey("tags.id", ondelete="CASCADE"),
        primary_key=True,
    )
