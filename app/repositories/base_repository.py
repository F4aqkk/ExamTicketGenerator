"""Базовый репозиторий с общими операциями."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.base import Base


class BaseRepository:
    """Общие операции создания, чтения, изменения и удаления."""

    def __init__(self, session: Session, model: type[Base]):
        """Запоминает сессию базы и модель, с которой работаем."""
        self.session = session
        self.model = model

    def create(self, **fields) -> Base:
        """Создать запись и сохранить ее в базе."""
        item = self.model(**fields)
        self.session.add(item)
        self.session.commit()
        return item

    def get_by_id(self, item_id: int) -> Base | None:
        """Найти запись по номеру. Если нет, вернуть None."""
        return self.session.get(self.model, item_id)

    def get_all(self) -> list[Base]:
        """Вернуть все записи таблицы."""
        return list(self.session.scalars(select(self.model)))

    def update(self, item: Base, **fields) -> Base:
        """Изменить указанные поля записи и сохранить."""
        for name, value in fields.items():
            setattr(item, name, value)
        self.session.commit()
        return item

    def delete(self, item: Base) -> None:
        """Удалить запись из базы."""
        self.session.delete(item)
        self.session.commit()
