from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Question(Base):
    __tablename__ = "questions"
    id: Mapped[int] = mapped_column(primary_key=True)
    text: Mapped[str] = mapped_column()
    answer: Mapped[str] = mapped_column()
    difficulty: Mapped[int] = mapped_column()
    task_type: Mapped[str] = mapped_column()
    topic_id: Mapped[int] = mapped_column(ForeignKey("topics.id"))
    created_at: Mapped[str] = mapped_column()
