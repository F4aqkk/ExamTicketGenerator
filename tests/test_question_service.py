"""Тесты бизнес-логики банка вопросов."""

import pytest

from app.repositories.question_repository import QuestionRepository
from app.repositories.topic_repository import TopicRepository
from app.services.generation_service import GenerationService
from app.services.question_service import (
    QuestionData,
    QuestionError,
    QuestionService,
    parse_tag_names,
)


def make_data(topic, **changes) -> QuestionData:
    """Правильные данные формы; отдельные поля можно заменить."""
    fields = {
        "text": "Что делает оператор JOIN?",
        "answer": "Соединяет строки двух таблиц.",
        "topic_id": topic.id,
        "task_type": "Теория",
        "difficulty": 2,
        "tag_names": "JOIN, подзапросы",
    }
    fields.update(changes)
    return QuestionData(**fields)


def test_parse_tag_names_cleans_line():
    """Строка тегов режется по запятым, лишнее и повторы убираются."""
    names = parse_tag_names(" JOIN, #подзапросы ,, join ,  ")

    assert names == ["JOIN", "подзапросы"]


def test_add_question_saves_fields_and_tags(session):
    """Вопрос сохраняется с ответом, темой и двумя тегами."""
    topic = TopicRepository(session).create(name="SQL")
    service = QuestionService(session)

    question = service.add_question(make_data(topic))

    assert question.id is not None
    assert question.answer == "Соединяет строки двух таблиц."
    assert question.topic.name == "SQL"
    assert [tag.name for tag in question.tags] == ["JOIN", "подзапросы"]
    assert service.count() == 1


def test_existing_tag_is_reused_ignoring_case(session):
    """Тег «sql» не создаётся заново, если в базе уже есть «SQL»."""
    topic = TopicRepository(session).create(name="SQL")
    service = QuestionService(session)
    service.tags.create(name="SQL")

    question = service.add_question(make_data(topic, tag_names="sql"))

    assert [tag.name for tag in question.tags] == ["SQL"]
    assert len(service.get_tags()) == 1


def test_answer_may_be_empty(session):
    """Вопрос без ответа сохраняется, ответ хранится пустой строкой."""
    topic = TopicRepository(session).create(name="SQL")
    service = QuestionService(session)

    question = service.add_question(make_data(topic, answer="  "))

    assert question.answer == ""


@pytest.mark.parametrize(
    "changes, message",
    [
        ({"text": "   "}, "Введите текст вопроса."),
        ({"topic_id": None}, "Выберите тему."),
        ({"topic_id": 999}, "Выберите тему."),
        ({"task_type": ""}, "Выберите тип задания."),
        ({"difficulty": 0}, "Выберите сложность."),
    ],
    ids=["no_text", "no_topic", "unknown_topic", "no_type", "no_level"],
)
def test_wrong_data_is_rejected(session, changes, message):
    """Неполные данные формы не сохраняются, сообщение понятное."""
    topic = TopicRepository(session).create(name="SQL")
    service = QuestionService(session)

    with pytest.raises(QuestionError, match=message):
        service.add_question(make_data(topic, **changes))

    assert service.count() == 0


def test_update_question_replaces_fields_and_tags(session):
    """При изменении вопроса меняются поля и набор тегов."""
    topic = TopicRepository(session).create(name="SQL")
    service = QuestionService(session)
    question = service.add_question(make_data(topic))

    service.update_question(
        question,
        make_data(topic, text="Новый текст", tag_names="SELECT"),
    )

    assert question.text == "Новый текст"
    assert [tag.name for tag in question.tags] == ["SELECT"]


def test_delete_question(session):
    """Вопрос, которого нет в билетах, удаляется."""
    topic = TopicRepository(session).create(name="SQL")
    service = QuestionService(session)
    question = service.add_question(make_data(topic))

    service.delete_question(question)

    assert service.count() == 0


def test_question_from_saved_ticket_is_not_deleted(session):
    """Вопрос из сохранённого билета не удаляется, сообщение понятное."""
    topic = TopicRepository(session).create(name="SQL")
    service = QuestionService(session)
    question = service.add_question(make_data(topic))
    generations = GenerationService(session)
    generations.create("Зачёт", 1, {2: 1})

    with pytest.raises(QuestionError, match="в сохранённых билетах"):
        service.delete_question(question)

    assert service.count() == 1  # после ошибки с базой можно работать
    assert generations.count() == 1


def test_add_topic_returns_existing_and_rejects_empty(session):
    """Тема с тем же названием не дублируется, пустая не принимается."""
    service = QuestionService(session)
    first = service.add_topic(" Нормализация ")

    second = service.add_topic("нормализация")

    assert second.id == first.id
    assert [topic.name for topic in service.get_topics()] == ["Нормализация"]
    with pytest.raises(QuestionError, match="Введите название темы."):
        service.add_topic("   ")


def test_search_finds_question_by_tag_name(session):
    """Поиск по тексту смотрит и в названия тегов вопроса."""
    topic = TopicRepository(session).create(name="SQL")
    service = QuestionService(session)
    service.add_question(make_data(topic, text="Первый", tag_names="JOIN"))
    service.add_question(make_data(topic, text="Второй", tag_names=""))

    found = QuestionRepository(session).search(text="join")

    assert [question.text for question in found] == ["Первый"]
