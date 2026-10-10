"""Бизнес-логика банка вопросов: проверки, темы и теги.

Окна программы не обращаются к базе напрямую, а вызывают этот сервис.
Сервис проверяет введённые данные и просит репозитории сохранить их.
"""

from dataclasses import dataclass

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.question import Question
from app.models.tag import Tag
from app.models.topic import Topic
from app.repositories.question_repository import QuestionRepository
from app.repositories.tag_repository import TagRepository
from app.repositories.topic_repository import TopicRepository

BANK_LIMIT = 1500  # на столько вопросов рассчитан банк (из ТЗ)
TASK_TYPES = ("Теория", "Практика")
DIFFICULTY_NAMES = {
    0: "Не задана",
    1: "Лёгкий",
    2: "Средний",
    3: "Сложный",
}


class QuestionError(Exception):
    """Ошибка с понятным текстом, который можно показать в окне."""


@dataclass
class QuestionData:
    """То, что преподаватель ввёл в форме вопроса."""

    text: str  # текст вопроса
    answer: str  # ответ; может быть пустым
    topic_id: int | None  # номер темы; None = тема не выбрана
    task_type: str  # «Теория» или «Практика»
    difficulty: int  # 1 лёгкий, 2 средний, 3 сложный
    tag_names: str = ""  # теги одной строкой через запятую


def parse_tag_names(line: str) -> list[str]:
    """Разобрать строку «JOIN, подзапросы» в список названий тегов.

    Пробелы по краям и знак # в начале убираются, пустые названия
    и повторы (без учёта регистра) пропускаются.
    """
    names: list[str] = []
    seen: set[str] = set()  # уже встреченные названия строчными буквами
    for part in line.split(","):
        name = part.strip().lstrip("#").strip()
        if name and name.casefold() not in seen:
            seen.add(name.casefold())
            names.append(name)
    return names


class QuestionService:
    """Операции с банком вопросов для окон программы."""

    def __init__(self, session: Session):
        """Запоминает сессию и создаёт репозитории вопросов, тем и тегов."""
        self.session = session
        self.questions = QuestionRepository(session)
        self.topics = TopicRepository(session)
        self.tags = TagRepository(session)

    def count(self) -> int:
        """Сколько вопросов в банке."""
        return self.questions.count()

    def get_topics(self) -> list[Topic]:
        """Все темы по алфавиту."""
        return sorted(self.topics.get_all(), key=lambda t: t.name.casefold())

    def get_tags(self) -> list[Tag]:
        """Все теги по алфавиту."""
        return sorted(self.tags.get_all(), key=lambda t: t.name.casefold())

    def search(
        self,
        text: str = "",
        difficulty: int | None = None,
        topic_id: int | None = None,
        tag_id: int | None = None,
    ) -> list[Question]:
        """Вопросы для таблицы с учётом поиска и фильтров."""
        return self.questions.search(text, difficulty, topic_id, tag_id)

    def add_topic(self, name: str) -> Topic:
        """Добавить тему. Если такая уже есть, вернуть её.

        Пустое название не принимается: будет ошибка для показа в окне.
        """
        name = name.strip()
        if not name:
            raise QuestionError("Введите название темы.")
        for topic in self.topics.get_all():
            if topic.name.casefold() == name.casefold():
                return topic
        return self.topics.create(name=name)

    def add_question(self, data: QuestionData) -> Question:
        """Проверить данные формы и добавить вопрос вместе с тегами."""
        self._check(data)
        return self._save(Question(), data)

    def update_question(
        self,
        question: Question,
        data: QuestionData,
    ) -> Question:
        """Проверить данные формы и изменить вопрос и его теги."""
        self._check(data)
        return self._save(question, data)

    def delete_question(self, question: Question) -> None:
        """Удалить вопрос.

        Вопрос, который стоит в сохранённом билете, база удалить
        не даёт. Тогда изменения отменяются и выдаётся ошибка
        с понятным текстом.
        """
        try:
            self.questions.delete(question)
        except IntegrityError:
            self.session.rollback()
            raise QuestionError(
                "Этот вопрос стоит в сохранённых билетах, "
                "поэтому удалить его нельзя."
            ) from None

    def _check(self, data: QuestionData) -> None:
        """Проверить данные формы; при ошибке сообщить, что исправить."""
        if not data.text.strip():
            raise QuestionError("Введите текст вопроса.")
        if data.topic_id is None or not self.topics.get_by_id(data.topic_id):
            raise QuestionError("Выберите тему.")
        if not data.task_type.strip():
            raise QuestionError("Выберите тип задания.")
        if data.difficulty not in (1, 2, 3):
            raise QuestionError("Выберите сложность.")

    def _save(self, question: Question, data: QuestionData) -> Question:
        """Перенести данные формы в вопрос и записать одной транзакцией.

        Вопрос и новые теги сохраняются вместе: если что-то не
        записалось, отменяются все изменения.
        """
        try:
            tags = self._find_or_make_tags(data.tag_names)
            question.text = data.text.strip()
            question.answer = data.answer.strip()
            question.topic_id = data.topic_id
            question.task_type = data.task_type.strip()
            question.difficulty = data.difficulty
            question.tags = tags
            self.session.add(question)  # для нового вопроса; старый уже там
            self.session.commit()
        except Exception:
            self.session.rollback()  # ошибка: отменить все изменения
            raise  # и сообщить об ошибке дальше
        return question

    def _find_or_make_tags(self, line: str) -> list[Tag]:
        """Теги по строке названий: есть в базе — берём, нет — создаём."""
        known = {tag.name.casefold(): tag for tag in self.tags.get_all()}
        tags = []
        for name in parse_tag_names(line):
            tags.append(known.get(name.casefold()) or Tag(name=name))
        return tags
