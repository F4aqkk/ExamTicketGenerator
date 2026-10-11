"""Тесты сохранения генерации, билетов и вопросов билетов."""

import pytest
from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError

from app.models.generation import Generation
from app.models.ticket_question import TicketQuestion
from app.repositories.generation_repository import GenerationRepository
from app.repositories.question_repository import QuestionRepository
from app.repositories.ticket_repository import TicketRepository
from app.repositories.topic_repository import TopicRepository
from app.services.generation_service import (
    GenerationError,
    GenerationService,
)


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


def test_ticket_number_is_unique_in_generation(session):
    """Второй билет с тем же номером в генерации не сохранится (UNIQUE)."""
    fill_bank(session)
    generation = GenerationService(session).create("Экзамен", 2, {1: 1})

    with pytest.raises(IntegrityError):
        TicketRepository(session).create(
            generation_id=generation.id,
            number=1,
        )


def test_database_deletes_tickets_itself(session):
    """Удаление генерации прямым запросом: билеты удаляет база (CASCADE)."""
    fill_bank(session)
    GenerationService(session).create("Экзамен", 3, {1: 1})
    session.expunge_all()  # забыть объекты: пусть работает только база

    session.execute(delete(Generation))
    session.commit()

    assert TicketRepository(session).get_all() == []
    assert session.scalars(select(TicketQuestion)).all() == []


def test_question_in_saved_ticket_cannot_be_deleted(session):
    """Вопрос из сохранённого билета удалить нельзя (RESTRICT)."""
    fill_bank(session)
    generation = GenerationService(session).create("Экзамен", 1, {1: 1})
    question = generation.tickets[0].ticket_questions[0].question

    with pytest.raises(IntegrityError):
        QuestionRepository(session).delete(question)


def test_available_counts_questions_by_difficulty(session):
    """Считается, сколько вопросов каждой сложности в выбранных темах."""
    fill_bank(session)
    other = TopicRepository(session).create(name="Git")
    QuestionRepository(session).create(
        text="Что делает команда git commit?",
        answer="Сохраняет изменения в истории проекта.",
        difficulty=1,
        task_type="Теория",
        topic_id=other.id,
    )
    service = GenerationService(session)

    assert service.available() == {1: 5, 2: 4, 3: 4}
    assert service.available([other.id]) == {1: 1, 2: 0, 3: 0}


def test_generate_saves_tickets_for_chosen_topics(session):
    """Правила выполнены: билеты составлены и попали в историю."""
    fill_bank(session)
    topic = TopicRepository(session).get_by_name("SQL")
    service = GenerationService(session)

    generation = service.generate(
        "  Экзамен  ",
        3,
        {1: 2, 2: 1, 3: 0},
        [topic.id],
    )

    assert generation.title == "Экзамен"
    assert generation.questions_per_ticket == 3
    assert service.history() == [generation]
    assert service.topic_names(generation) == ["SQL"]


@pytest.mark.parametrize(
    ("title", "tickets_count", "counts", "has_topics", "message"),
    [
        ("", 1, {1: 1}, True, "Введите название работы."),
        ("Экзамен", 1, {1: 1}, False, "Выберите хотя бы одну тему."),
        ("Экзамен", 0, {1: 1}, True, "от 1 до 100"),
        ("Экзамен", 101, {1: 1}, True, "от 1 до 100"),
        ("Экзамен", 1, {1: 0, 2: 0}, True, "хотя бы один вопрос"),
        ("Экзамен", 1, {3: 5}, True, "Не хватает сложных вопросов"),
    ],
)
def test_generate_rejects_wrong_rules(
    session,
    title,
    tickets_count,
    counts,
    has_topics,
    message,
):
    """Нарушено правило: ошибка с понятным текстом, в истории пусто."""
    fill_bank(session)
    topic = TopicRepository(session).get_by_name("SQL")
    service = GenerationService(session)
    topic_ids = [topic.id] if has_topics else []

    with pytest.raises(GenerationError, match=message):
        service.generate(title, tickets_count, counts, topic_ids)

    assert service.count() == 0


def test_delete_removes_generation_from_history(session):
    """Удалённая генерация пропадает из истории вместе с билетами."""
    fill_bank(session)
    service = GenerationService(session)
    generation = service.create("Экзамен", 2, {1: 1})

    service.delete(generation)

    assert service.history() == []
    assert TicketRepository(session).get_all() == []
