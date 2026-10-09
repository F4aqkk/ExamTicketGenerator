"""Сохранение генерации: критерии, билеты и вопросы билетов."""

from sqlalchemy.orm import Session

from app.models.generation import Generation
from app.models.ticket import Ticket
from app.models.ticket_question import TicketQuestion
from app.repositories.question_repository import QuestionRepository
from app.services.ticket_generator import TicketGenerator


class GenerationService:
    """Составляет билеты и сохраняет их в базу одной транзакцией."""

    def __init__(self, session: Session):
        """Запоминает сессию и создаёт генератор билетов."""
        self.session = session
        self.generator = TicketGenerator(QuestionRepository(session))

    def create(
        self,
        title: str,  # название, например «Экзамен ИСП 34»
        tickets_count: int,  # сколько билетов
        counts: dict[int, int],  # {сложность: сколько вопросов в билете}
        topic_ids: list[int] | None = None,  # None = из всех тем
    ) -> Generation:
        """Составить билеты и сохранить всё сразу.

        Сохраняется одна строка генерации, по строке на каждый билет
        и по строке на каждый вопрос каждого билета.
        Если хоть одна запись не сохранится, не сохранится ничего.
        """
        tickets = self.generator.generate(tickets_count, counts, topic_ids)
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
