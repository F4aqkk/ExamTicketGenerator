"""Репозиторий тегов."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.tag import Tag
from app.repositories.base_repository import BaseRepository


class TagRepository(BaseRepository):
    """Работа с таблицей тегов."""

    def __init__(self, session: Session):
        """Запоминает сессию базы данных."""
        super().__init__(session, Tag)

    def get_by_name(self, name: str) -> Tag | None:
        """Найти тег по названию. Если нет, то вернуть None."""
        query = select(Tag).where(Tag.name == name)
        return self.session.scalars(query).first()
