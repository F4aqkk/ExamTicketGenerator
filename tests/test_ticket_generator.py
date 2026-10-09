"""Тесты генератора билетов."""

import pytest

from app.repositories.question_repository import QuestionRepository
from app.repositories.topic_repository import TopicRepository
from app.services.ticket_generator import (
    NotEnoughQuestionsError,
    TicketGenerator,
)


def add_questions(session, topic_id, difficulty, count):
    """Добавить в базу нужное количество вопросов одной сложности."""
    repo = QuestionRepository(session)
    for i in range(count):
        repo.create(
            text=f"Вопрос {difficulty}-{i}",
            answer="Ответ",
            difficulty=difficulty,
            task_type="Теория",
            topic_id=topic_id,
        )


def test_ticket_has_no_repeats(session):
    """В одном билете вопросы не повторяются."""
    topic = TopicRepository(session).create(name="SQL")
    add_questions(session, topic.id, 1, 5)
    generator = TicketGenerator(QuestionRepository(session))

    tickets = generator.generate(10, {1: 3})

    for ticket in tickets:
        assert len(ticket) == 3
        assert len(set(q.id for q in ticket)) == 3


def test_not_enough_questions_raises_error(session):
    """Если вопросов меньше, чем нужно в билет, будет ошибка."""
    topic = TopicRepository(session).create(name="SQL")
    add_questions(session, topic.id, 2, 2)
    generator = TicketGenerator(QuestionRepository(session))

    with pytest.raises(NotEnoughQuestionsError):
        generator.generate(1, {2: 3})


def test_topic_filter(session):
    """Если выбрана тема, вопросы берутся только из неё."""
    topics = TopicRepository(session)
    sql = topics.create(name="SQL")
    python = topics.create(name="Python")
    add_questions(session, sql.id, 1, 5)
    add_questions(session, python.id, 1, 5)
    generator = TicketGenerator(QuestionRepository(session))

    tickets = generator.generate(5, {1: 2}, topic_ids=[python.id])

    for ticket in tickets:
        for question in ticket:
            assert question.topic_id == python.id


def test_tickets_count_and_difficulties(session):
    """Билетов столько, сколько просили, в каждом нужные сложности."""
    topic = TopicRepository(session).create(name="SQL")
    for difficulty in (1, 2, 3):
        add_questions(session, topic.id, difficulty, 3)
    generator = TicketGenerator(QuestionRepository(session))

    tickets = generator.generate(7, {1: 1, 2: 1, 3: 1})

    assert len(tickets) == 7
    for ticket in tickets:
        assert sorted(q.difficulty for q in ticket) == [1, 2, 3]
