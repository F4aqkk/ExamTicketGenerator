"""Генератор билетов из банка вопросов."""

import random  # модуль случайных чисел

from app.models.question import Question
from app.repositories.question_repository import QuestionRepository


class NotEnoughQuestionsError(Exception):  # свой вид ошибки
    """В банке не хватает вопросов нужной сложности."""


class TicketGenerator:
    """Составляет билеты из вопросов банка."""

    def __init__(self, question_repo: QuestionRepository):
        """Запоминает репозиторий, из которого берутся вопросы."""
        self.question_repo = question_repo  # через него берём вопросы

    def generate(
        self,
        tickets_count: int,  # сколько билетов нужно
        counts: dict[int, int],  # {сложность: сколько вопросов в билете}
        topic_ids: list[int] | None = None,  # из каких тем; None = из всех
    ) -> list[list[Question]]:
        """Составить билеты; каждый билет это список вопросов.

        Пример counts: {1: 5, 2: 5, 3: 5} значит 5 лёгких, 5 средних
        и 5 сложных вопросов в каждом билете.
        """
        tickets = [[] for _ in range(tickets_count)]  # пустые билеты
        for difficulty, amount in counts.items():
            questions = self.question_repo.find(difficulty, topic_ids)
            if len(questions) < amount:  # вопросов меньше, чем надо в билет
                raise NotEnoughQuestionsError(
                    f"Сложность {difficulty}: нужно {amount}, "
                    f"в банке {len(questions)}"
                )
            queue = []  # очередь перемешанных вопросов
            for ticket in tickets:
                ticket.extend(self._take(queue, questions, amount))
        return tickets

    @staticmethod
    def _take(queue, questions, amount):
        """Взять из очереди amount разных вопросов."""
        chosen = []  # вопросы для одного билета
        while len(chosen) < amount:
            if not queue:  # очередь кончилась: перемешать вопросы заново
                queue.extend(questions)
                random.shuffle(queue)
            question = queue.pop()  # вытащить последний из очереди
            if question not in chosen:  # в одном билете без повторов
                chosen.append(question)
        return chosen
