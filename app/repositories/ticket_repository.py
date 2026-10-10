"""Репозиторий билетов."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.ticket import Ticket
from app.repositories.base_repository import BaseRepository


class TicketRepository(BaseRepository):
    """Работа с таблицей билетов."""

    def __init__(self, session: Session):
        """Запоминает сессию базы данных."""
        super().__init__(session, Ticket)

    def get_by_generation(self, generation_id: int) -> list[Ticket]:
        """Билеты одной генерации по порядку номеров."""
        query = (
            select(Ticket)
            .where(Ticket.generation_id == generation_id)
            .order_by(Ticket.number)
        )
        return list(self.session.scalars(query))
