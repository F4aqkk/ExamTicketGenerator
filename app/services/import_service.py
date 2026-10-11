"""Импорт вопросов в банк из файлов DOCX, PDF, XLSX, TXT.

Файл должен быть записан по шаблону, как его сохраняет экспорт банка.
В таблице XLSX первая строка содержит названия столбцов: Тема,
Сложность, Тип задания, Вопрос, Ответ, Теги. В остальных форматах
каждый вопрос записан строками «Поле: значение», а вопросы
отделены друг от друга пустой строкой.
"""

from dataclasses import dataclass
from pathlib import Path

from sqlalchemy.orm import Session

from app.models.question import Question
from app.models.tag import Tag
from app.models.topic import Topic
from app.repositories.question_repository import QuestionRepository
from app.repositories.tag_repository import TagRepository
from app.repositories.topic_repository import TopicRepository
from app.services.documents import (
    TABLE_FORMAT,
    DocumentError,
    file_format,
    read_lines,
    read_table,
)
from app.services.question_service import TASK_TYPES, parse_tag_names

# Название поля в файле (строчными буквами) -> что это за поле.
FIELDS = {
    "тема": "topic",
    "сложность": "difficulty",
    "тип задания": "task_type",
    "теги": "tags",
    "вопрос": "text",
    "ответ": "answer",
}
# С чего начинается слово сложности -> её номер.
DIFFICULTY_WORDS = {"лег": 1, "сред": 2, "слож": 3}
NO_TOPIC = "Без темы"  # сюда попадают вопросы, у которых тема не указана
NO_HEADER = (
    "В первой строке таблицы должны быть названия столбцов: "
    "Тема, Сложность, Тип задания, Вопрос, Ответ, Теги."
)
NO_QUESTIONS = (
    "В файле не найдено ни одного вопроса. Каждый вопрос должен быть "
    "записан строками вида «Вопрос: текст», «Тема: название»."
)


@dataclass
class ImportResult:
    """Итог импорта: сколько вопросов добавлено и сколько пропущено."""

    added: int = 0  # добавлено в банк
    duplicates: int = 0  # пропущено: такой вопрос в этой теме уже есть
    empty: int = 0  # пропущено: нет текста вопроса
    no_difficulty: int = 0  # добавлено с отметкой «сложность не задана»


def parse_difficulty(value: str) -> int:
    """Сложность из файла: 1, 2 или 3; если не распознана, то 0.

    Понимает цифры и слова в любой форме: «лёгкий», «Средняя»,
    «сложные».
    """
    word = value.strip().casefold().replace("ё", "е")
    if word in ("1", "2", "3"):
        return int(word)
    for start, level in DIFFICULTY_WORDS.items():
        if word.startswith(start):
            return level
    return 0


def parse_task_type(value: str) -> str:
    """Тип задания из файла: «Практика» или, если не указан, «Теория»."""
    for task_type in TASK_TYPES:
        if value.strip().casefold() == task_type.casefold():
            return task_type
    return TASK_TYPES[0]


def parse_blocks(lines: list[str], joiner: str = "\n") -> list[dict[str, str]]:
    """Разобрать строки «Поле: значение» на вопросы.

    Вопрос кончается пустой строкой или когда поле встретилось
    второй раз. Строка без названия поля продолжает предыдущее поле:
    так читаются длинные тексты, перенесённые на несколько строк.
    """
    records = []
    record: dict[str, str] = {}
    last = ""  # поле, которое читали последним
    for raw in lines:
        line = raw.strip()
        name, colon, value = line.partition(":")
        field = FIELDS.get(name.strip().casefold()) if colon else None
        if not line or (field and field in record):
            if record:  # вопрос кончился
                records.append(record)
            record = {}
            last = ""
        if field:
            record[field] = value.strip()
            last = field
        elif line and last:
            record[last] += joiner + line
    if record:
        records.append(record)
    return records


def parse_table(rows: list[list[str]]) -> list[dict[str, str]]:
    """Разобрать строки таблицы на вопросы по названиям столбцов."""
    if not rows:
        raise DocumentError(NO_HEADER)
    columns = [FIELDS.get(name.strip().casefold()) for name in rows[0]]
    if "text" not in columns:
        raise DocumentError(NO_HEADER)
    records = []
    for row in rows[1:]:
        record = {}
        for field, value in zip(columns, row):
            if field:
                record[field] = value
        if any(record.values()):  # полностью пустые строки пропускаем
            records.append(record)
    return records


class ImportService:
    """Читает вопросы из файла и добавляет их в банк."""

    def __init__(self, session: Session):
        """Запоминает сессию и создаёт репозитории вопросов, тем, тегов."""
        self.session = session
        self.questions = QuestionRepository(session)
        self.topics = TopicRepository(session)
        self.tags = TagRepository(session)
        self._topics: dict[str, Topic] = {}  # темы по названиям
        self._tags: dict[str, Tag] = {}  # теги по названиям

    def import_bank(self, path: str | Path) -> ImportResult:
        """Добавить в банк вопросы из файла и сообщить итог.

        Все вопросы файла сохраняются одной транзакцией: при ошибке
        в банк не попадает ни один.
        """
        records = self._read(path)
        if not records:
            raise DocumentError(NO_QUESTIONS)
        try:
            result = self._add(records)
            self.session.commit()
        except Exception:
            self.session.rollback()  # ошибка: отменить все изменения
            raise  # и сообщить об ошибке дальше
        return result

    @staticmethod
    def _read(path: str | Path) -> list[dict[str, str]]:
        """Прочитать файл и разобрать его на вопросы."""
        kind = file_format(path)
        if kind == TABLE_FORMAT:
            return parse_table(read_table(path))
        # В PDF длинная строка разбита на несколько: склеиваем пробелом.
        joiner = " " if kind == "PDF" else "\n"
        return parse_blocks(read_lines(path), joiner)

    def _add(self, records: list[dict[str, str]]) -> ImportResult:
        """Положить разобранные вопросы в сессию и посчитать итог."""
        result = ImportResult()
        self._topics = self._by_name(self.topics.get_all())
        self._tags = self._by_name(self.tags.get_all())
        known = set()  # приметы вопросов, которые уже есть в банке
        for question in self.questions.search():
            known.add(self._key(question.topic.name, question.text))
        for record in records:
            text = record.get("text", "").strip()
            topic_name = record.get("topic", "").strip() or NO_TOPIC
            key = self._key(topic_name, text)
            if not text:
                result.empty += 1
            elif key in known:
                result.duplicates += 1
            else:
                known.add(key)
                question = self._make_question(record, text, topic_name)
                self.session.add(question)
                result.added += 1
                if question.difficulty == 0:
                    result.no_difficulty += 1
        return result

    def _make_question(
        self,
        record: dict[str, str],
        text: str,
        topic_name: str,
    ) -> Question:
        """Собрать вопрос из записи файла; тема и теги ищутся по названию.

        Если темы или тега с таким названием ещё нет, они создаются.
        """
        topic = self._topics.get(topic_name.casefold())
        if topic is None:
            topic = Topic(name=topic_name)
            self._topics[topic_name.casefold()] = topic
        question = Question(
            text=text,
            answer=record.get("answer", "").strip(),
            difficulty=parse_difficulty(record.get("difficulty", "")),
            task_type=parse_task_type(record.get("task_type", "")),
            topic=topic,
        )
        for name in parse_tag_names(record.get("tags", "")):
            tag = self._tags.get(name.casefold())
            if tag is None:
                tag = Tag(name=name)
                self._tags[name.casefold()] = tag
            question.tags.append(tag)
        return question

    @staticmethod
    def _by_name(items: list) -> dict:
        """Словарь «название строчными буквами -> тема или тег»."""
        return {item.name.casefold(): item for item in items}

    @staticmethod
    def _key(topic_name: str, text: str) -> tuple[str, str]:
        """Примета вопроса для поиска повторов: тема и текст.

        Регистр букв и лишние пробелы не учитываются.
        """
        return topic_name.casefold(), " ".join(text.split()).casefold()
