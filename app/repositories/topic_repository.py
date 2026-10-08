"""Репозиторий тем."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.topic import Topic
from app.repositories.base_repository import BaseRepository


class TopicRepository(BaseRepository):
    """Работа с таблицей тем."""

    def __init__(self, session: Session):
        """Запоминает сессию базы данных."""
        super().__init__(session, Topic)

    def get_by_name(self, name: str) -> Topic | None:
        """Найти тему по названию. Если нет, то вернуть None."""
        query = select(Topic).where(Topic.name == name)
        return self.session.scalars(query).first()
