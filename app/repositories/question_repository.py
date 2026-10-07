from sqlalchemy import select  # select = «выбрать» строки из таблицы
from sqlalchemy.orm import Session  # нужна для подсказки типа

from app.models.question import Question  # модель вопроса
from app.repositories.base_repository import BaseRepository


class QuestionRepository(BaseRepository):  # наследует create, update и др.
    """Работа с таблицей вопросов."""

    def __init__(self, session: Session):
        super().__init__(session, Question)  # родителю: сессия и модель

    def find(
        self,
        difficulty: int,  # сложность: 1, 2 или 3
        topic_ids: list[int] | None = None,  # номера тем; None = любые
    ) -> list[Question]:
        """Найти вопросы заданной сложности, при желании только из тем."""
        query = select(Question).where(Question.difficulty == difficulty)
        if topic_ids:  # если список тем задан и не пустой
            query = query.where(Question.topic_id.in_(topic_ids))  # + условие
        return list(self.session.scalars(query))  # выполнить, вернуть список
