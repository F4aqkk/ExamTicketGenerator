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


def test_questions_without_difficulty_are_not_used(session):
    """Вопросы со сложностью 0 («не задана») в билеты не попадают."""
    topic = TopicRepository(session).create(name="SQL")
    add_questions(session, topic.id, 0, 5)
    add_questions(session, topic.id, 1, 2)
    generator = TicketGenerator(QuestionRepository(session))

    tickets = generator.generate(3, {1: 2})

    for ticket in tickets:
        assert all(q.difficulty == 1 for q in ticket)


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


def test_mix_topics_puts_different_topics_into_ticket(session):
    """При выборе разных тем в билете нет двух вопросов одной темы."""
    topics = TopicRepository(session)
    for name in ("SQL", "Git", "Python"):
        add_questions(session, topics.create(name=name).id, 1, 3)
    generator = TicketGenerator(QuestionRepository(session))

    tickets = generator.generate(3, {1: 3}, mix_topics=True)

    for ticket in tickets:
        assert len({question.topic_id for question in ticket}) == 3


def test_tickets_without_no_repeat_rule_are_still_correct(session):
    """Без правила «не повторять» в каждом билете всё равно нет повторов."""
    topic = TopicRepository(session).create(name="SQL")
    add_questions(session, topic.id, 1, 4)
    generator = TicketGenerator(QuestionRepository(session))

    tickets = generator.generate(5, {1: 3}, no_repeat=False)

    assert len(tickets) == 5
    for ticket in tickets:
        assert len(set(ticket)) == 3


def test_mix_topics_keeps_topics_in_turns(session):
    """С правилом «Разные темы» темы чередуются по всему билету."""
    topics = TopicRepository(session)
    made = [topics.create(name=name) for name in ("SQL", "Python", "Git")]
    for topic in made:
        add_questions(session, topic.id, 1, 10)
    generator = TicketGenerator(QuestionRepository(session))

    ticket = generator.generate(1, {1: 9}, mix_topics=True)[0]

    counts = {topic.id: 0 for topic in made}
    for question in ticket:
        counts[question.topic_id] += 1
    assert sorted(counts.values()) == [3, 3, 3]


def test_mix_topics_starts_new_round_of_topics(session):
    """Круг тем начинается заново: первые три темы идут и дальше."""
    topics = TopicRepository(session)
    made = [topics.create(name=name) for name in ("SQL", "Python", "Git")]
    for topic in made:
        add_questions(session, topic.id, 1, 10)
    generator = TicketGenerator(QuestionRepository(session))

    ticket = generator.generate(1, {1: 6}, mix_topics=True)[0]

    first_round = {question.topic_id for question in ticket[:3]}
    second_round = {question.topic_id for question in ticket[3:]}
    assert len(first_round) == 3  # в первом круге все три темы
    assert first_round == second_round  # и во втором тоже все три
