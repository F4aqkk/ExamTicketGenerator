"""Репозиторий вопросов."""

from sqlalchemy import select  # select = «выбрать» строки из таблицы
from sqlalchemy.orm import Session  # нужна для подсказки типа

from app.models.question import Question  # модель вопроса
from app.models.tag import Tag
from app.repositories.base_repository import BaseRepository


class QuestionRepository(BaseRepository):  # наследует create, update и др.
    """Работа с таблицей вопросов."""

    def __init__(self, session: Session):
        """Запоминает сессию базы данных."""
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

    def search(
        self,
        text: str = "",  # слово или часть слова; "" = без поиска
        difficulty: int | None = None,  # None = любая сложность
        topic_id: int | None = None,  # None = любая тема
        tag_id: int | None = None,  # None = любой тег
    ) -> list[Question]:
        """Поиск и фильтры для списка вопросов.

        Незаданные условия не учитываются. Текст ищется без учёта
        регистра: «sql» найдёт и «SQL», «запрос» найдёт «Запрос».
        """
        query = select(Question).order_by(Question.id)
        if difficulty is not None:
            query = query.where(Question.difficulty == difficulty)
        if topic_id is not None:
            query = query.where(Question.topic_id == topic_id)
        if tag_id is not None:  # у вопроса есть хотя бы один такой тег
            query = query.where(Question.tags.any(Tag.id == tag_id))
        questions = list(self.session.scalars(query))
        if text:
            # SQLite умеет без учёта регистра сравнивать только латиницу,
            # поэтому текст сравниваем в Python: casefold() делает
            # строчными любые буквы, и русские тоже.
            needle = text.casefold()
            questions = [q for q in questions if needle in q.text.casefold()]
        return questions

    def add_tag(self, question: Question, tag: Tag) -> None:
        """Привязать тег к вопросу (строка в таблице «вопрос–тег»)."""
        if tag not in question.tags:  # второй раз тот же тег не нужен
            question.tags.append(tag)
            self.session.commit()

    def remove_tag(self, question: Question, tag: Tag) -> None:
        """Отвязать тег от вопроса (строка «вопрос–тег» удаляется)."""
        if tag in question.tags:
            question.tags.remove(tag)
            self.session.commit()
