"""Тесты сохранения генерации, билетов и вопросов билетов."""

import pytest
from sqlalchemy.exc import IntegrityError

from app.repositories.generation_repository import GenerationRepository
from app.repositories.question_repository import QuestionRepository
from app.repositories.ticket_repository import TicketRepository
from app.repositories.topic_repository import TopicRepository
from app.services.generation_service import GenerationService


def fill_bank(session):
    """Банк: по 4 вопроса каждой сложности в одной теме."""
    topic = TopicRepository(session).create(name="SQL")
    repo = QuestionRepository(session)
    for difficulty in (1, 2, 3):
        for i in range(4):
            repo.create(
                text=f"Вопрос {difficulty}-{i}",
                answer="Ответ",
                difficulty=difficulty,
                task_type="Теория",
                topic_id=topic.id,
            )


def test_generation_is_saved_with_tickets(session):
    """Сохраняются генерация, её билеты и вопросы билетов."""
    fill_bank(session)
    service = GenerationService(session)

    generation = service.create("Экзамен", 3, {1: 1, 2: 1, 3: 1})

    saved = GenerationRepository(session).get_by_id(generation.id)
    assert saved.questions_per_ticket == 3
    assert [t.number for t in saved.tickets] == [1, 2, 3]
    first = saved.tickets[0]
    assert [tq.position for tq in first.ticket_questions] == [1, 2, 3]
    assert first.ticket_questions[0].question.text.startswith("Вопрос")


def test_error_saves_nothing(session):
    """Ошибка при сохранении отменяет всё (транзакция, rollback)."""
    fill_bank(session)
    service = GenerationService(session)

    with pytest.raises(IntegrityError):  # 0 билетов запрещено CHECK
        service.create("Пустая", 0, {1: 1})

    assert GenerationRepository(session).get_all() == []
    assert TicketRepository(session).get_all() == []


def test_delete_generation_deletes_tickets(session):
    """Удалили генерацию, удалились и её билеты (cascade)."""
    fill_bank(session)
    generation = GenerationService(session).create("Экзамен", 2, {1: 2})
    tickets = TicketRepository(session)
    assert len(tickets.get_by_generation(generation.id)) == 2

    GenerationRepository(session).delete(generation)

    assert tickets.get_all() == []


def test_history_newest_first(session):
    """История генераций: последняя сверху."""
    fill_bank(session)
    service = GenerationService(session)
    service.create("Первая", 1, {1: 1})
    service.create("Вторая", 1, {1: 1})

    history = GenerationRepository(session).get_history()

    assert [g.title for g in history] == ["Вторая", "Первая"]
