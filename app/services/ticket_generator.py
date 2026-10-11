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
        no_repeat: bool = True,  # не повторять вопросы между билетами
        mix_topics: bool = False,  # стараться брать в билет разные темы
    ) -> list[list[Question]]:
        """Составить билеты; каждый билет это список вопросов.

        Пример количества вопросов по сложностям: {1: 5, 2: 5, 3: 5}
        значит 5 лёгких, 5 средних и 5 сложных вопросов в каждом билете.

        Если вопросы не повторяются, следующий билет берёт их из той же
        очереди, и вопрос встретится второй раз только когда кончатся
        неиспользованные. Иначе каждый билет набирается из всех вопросов
        заново. Разные темы берутся, пока это позволяет банк.
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
                if not no_repeat:
                    queue = []  # этот билет набирается из всех вопросов
                used_topics = None  # None = на темы не смотрим
                if mix_topics:  # темы, которые в билете уже есть
                    used_topics = {question.topic_id for question in ticket}
                taken = self._take(queue, questions, amount, used_topics)
                ticket.extend(taken)
        return tickets

    @classmethod
    def _take(cls, queue, questions, amount, used_topics=None):
        """Взять из очереди нужное количество разных вопросов.

        Если передан набор тем, которые в билете уже есть, сначала
        берутся вопросы из других тем.
        """
        chosen = []  # вопросы для одного билета
        while len(chosen) < amount:
            if not queue:  # очередь кончилась: перемешать вопросы заново
                queue.extend(questions)
                random.shuffle(queue)
            question = queue.pop(cls._position(queue, used_topics))
            if question not in chosen:  # в одном билете без повторов
                chosen.append(question)
                if used_topics is not None:
                    used_topics.add(question.topic_id)
        return chosen

    @staticmethod
    def _position(queue, used_topics) -> int:
        """Место в очереди, откуда взять следующий вопрос.

        Обычно это конец очереди. Если нужны разные темы, ищем
        с конца вопрос из темы, которой в билете ещё нет; если такого
        нет, берём последний.
        """
        last = len(queue) - 1
        if used_topics is None:
            return last
        for position in range(last, -1, -1):
            if queue[position].topic_id not in used_topics:
                return position
        return last
