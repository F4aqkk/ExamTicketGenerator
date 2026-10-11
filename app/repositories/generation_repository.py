"""Репозиторий генераций (история запусков генератора)."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.generation import Generation
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
