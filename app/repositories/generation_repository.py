"""Репозиторий генераций (история запусков генератора)."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.generation import Generation
from app.models.question import Question
from app.models.ticket import Ticket
from app.models.ticket_question import TicketQuestion
from app.models.topic import Topic
from app.repositories.base_repository import BaseRepository


class GenerationRepository(BaseRepository):
    """Работа с таблицей генераций."""

    def __init__(self, session: Session):
        """Запоминает сессию базы данных."""
        super().__init__(session, Generation)

    def get_history(self) -> list[Generation]:
        """Все генерации, последние сверху (для окна истории)."""
        query = select(Generation).order_by(Generation.id.desc())
        return list(self.session.scalars(query))

    def get_topic_names(self, generation_id: int) -> list[str]:
        """Названия тем, из которых взяты вопросы генерации, по алфавиту.

        Тема ищется по цепочке: билеты генерации, вопросы билетов,
        сами вопросы, их темы. Повторы убираются.
        """
        query = (
            select(Topic.name)
            .join(Question, Question.topic_id == Topic.id)
            .join(TicketQuestion, TicketQuestion.question_id == Question.id)
            .join(Ticket, Ticket.id == TicketQuestion.ticket_id)
            .where(Ticket.generation_id == generation_id)
            .distinct()
            .order_by(Topic.name)
        )
        return list(self.session.scalars(query))
