"""Генерации билетов: проверка правил, составление, сохранение, история.

Окна программы не обращаются к базе напрямую, а вызывают этот сервис.
"""

from sqlalchemy.orm import Session

from app.models.generation import Generation
from app.models.ticket import Ticket
from app.models.ticket_question import TicketQuestion
from app.repositories.generation_repository import GenerationRepository
from app.repositories.question_repository import QuestionRepository
from app.services.ticket_generator import TicketGenerator

MAX_TICKETS = 100  # больше билетов за один раз не составляется (из ТЗ)
LEVEL_WORDS = {1: "лёгких", 2: "средних", 3: "сложных"}


class GenerationError(Exception):
    """Ошибка с понятным текстом, который можно показать в окне."""


class GenerationService:
    """Составляет билеты и сохраняет их в базу одной транзакцией."""

    def __init__(self, session: Session):
        """Запоминает сессию, создаёт генератор и репозиторий генераций."""
        self.session = session
        self.generator = TicketGenerator(QuestionRepository(session))
        self.generations = GenerationRepository(session)

    def count(self) -> int:
        """Сколько генераций сохранено в истории."""
        return self.generations.count()

    def history(self) -> list[Generation]:
        """Все сохранённые генерации, последние сверху."""
        return self.generations.get_history()

    def topic_names(self, generation: Generation) -> list[str]:
        """Названия тем, из которых взяты вопросы этой генерации."""
        return self.generations.get_topic_names(generation.id)

    def delete(self, generation: Generation) -> None:
        """Удалить генерацию из истории вместе с её билетами."""
        self.generations.delete(generation)

    def available(self, topic_ids: list[int] | None = None) -> dict[int, int]:
        """Сколько вопросов каждой сложности есть в выбранных темах.

        Возвращает словарь: сложность -> количество вопросов.
        Если темы не переданы, считаются вопросы всех тем.
        """
        repo = self.generator.question_repo
        result = {}
        for difficulty in (1, 2, 3):
            result[difficulty] = len(repo.find(difficulty, topic_ids))
        return result

    def generate(
        self,
        title: str,  # название работы
        tickets_count: int,  # сколько билетов
        counts: dict[int, int],  # {сложность: сколько вопросов в билете}
        topic_ids: list[int],  # отмеченные темы
        no_repeat: bool = True,  # не повторять вопросы между билетами
        mix_topics: bool = False,  # стараться брать в билет разные темы
    ) -> Generation:
        """Проверить правила, составить билеты и сохранить их.

        Этот метод вызывает окно генератора. Если билеты составить
        нельзя, выдаётся ошибка с текстом, который объясняет причину.
        """
        title = title.strip()
        asked = {}  # только те сложности, вопросы которых нужны в билете
        for level, amount in counts.items():
            if amount > 0:
                asked[level] = amount
        self._check(title, tickets_count, asked, topic_ids)
        return self.create(
            title,
            tickets_count,
            asked,
            topic_ids,
            no_repeat,
            mix_topics,
        )

    def _check(
        self,
        title: str,
        tickets_count: int,
        counts: dict[int, int],
        topic_ids: list[int],
    ) -> None:
        """Проверить правила выборки; при ошибке сообщить, что исправить."""
        if not title:
            raise GenerationError("Введите название работы.")
        if not topic_ids:
            raise GenerationError("Выберите хотя бы одну тему.")
        if not 1 <= tickets_count <= MAX_TICKETS:
            raise GenerationError(
                f"Количество билетов должно быть от 1 до {MAX_TICKETS}."
            )
        if not counts:
            raise GenerationError("В билете должен быть хотя бы один вопрос.")
        available = self.available(topic_ids)
        for level, amount in counts.items():
            if available[level] < amount:
                raise GenerationError(
                    f"Не хватает {LEVEL_WORDS[level]} вопросов: в билет "
                    f"нужно {amount}, а в выбранных темах их "
                    f"{available[level]}."
                )

    def create(
        self,
        title: str,  # название, например «Экзамен ИСП 34»
        tickets_count: int,  # сколько билетов
        counts: dict[int, int],  # {сложность: сколько вопросов в билете}
        topic_ids: list[int] | None = None,  # None = из всех тем
        no_repeat: bool = True,  # не повторять вопросы между билетами
        mix_topics: bool = False,  # стараться брать в билет разные темы
    ) -> Generation:
        """Составить билеты и сохранить всё сразу.

        Сохраняется одна строка генерации, по строке на каждый билет
        и по строке на каждый вопрос каждого билета.
        Если хоть одна запись не сохранится, не сохранится ничего.
        """
        tickets = self.generator.generate(
            tickets_count,
            counts,
            topic_ids,
            no_repeat,
            mix_topics,
        )
        generation = Generation(
            title=title,
            tickets_count=tickets_count,
            questions_per_ticket=sum(counts.values()),
        )
        for number, questions in enumerate(tickets, start=1):
            ticket = Ticket(number=number)
            for position, question in enumerate(questions, start=1):
                ticket.ticket_questions.append(
                    TicketQuestion(question=question, position=position)
                )
            generation.tickets.append(ticket)
        self.session.add(generation)  # билеты добавятся вместе с ней
        try:
            self.session.commit()  # всё записывается одной транзакцией
        except Exception:
            self.session.rollback()  # ошибка: отменить все изменения
            raise  # и сообщить об ошибке дальше
        return generation
