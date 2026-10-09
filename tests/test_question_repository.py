"""Тесты вопросов: CRUD, поиск, фильтры, теги, ограничения."""

import pytest
from sqlalchemy.exc import IntegrityError

from app.repositories.question_repository import QuestionRepository
from app.repositories.tag_repository import TagRepository
from app.repositories.topic_repository import TopicRepository


def make_question(repo, topic, text="Что такое SQL?", difficulty=1):
    """Создать вопрос с нужным текстом и сложностью."""
    return repo.create(
        text=text,
        answer="Язык запросов к базам данных",
        difficulty=difficulty,
        task_type="Теория",
        topic_id=topic.id,
    )


def test_created_at_is_filled_by_default(session):
    """Дату создания ставит сама база (DEFAULT)."""
    topic = TopicRepository(session).create(name="SQL")

    question = make_question(QuestionRepository(session), topic)

    assert question.created_at is not None


def test_difficulty_must_be_from_0_to_3(session):
    """Сложность 4 база не сохраняет (CHECK)."""
    topic = TopicRepository(session).create(name="SQL")

    with pytest.raises(IntegrityError):
        make_question(QuestionRepository(session), topic, difficulty=4)


def test_difficulty_zero_means_not_set(session):
    """Сложность 0 сохраняется: это «не задана», такие вопросы ищутся."""
    topic = TopicRepository(session).create(name="SQL")
    repo = QuestionRepository(session)
    question = make_question(repo, topic, difficulty=0)

    assert repo.search(difficulty=0) == [question]


def test_update_and_delete_question(session):
    """Вопрос можно изменить и удалить."""
    topic = TopicRepository(session).create(name="SQL")
    repo = QuestionRepository(session)
    question = make_question(repo, topic)

    repo.update(question, answer="Structured Query Language")
    assert repo.get_by_id(question.id).answer == "Structured Query Language"

    repo.delete(question)
    assert repo.get_all() == []


def test_lazy_loading_topic_and_questions(session):
    """Связанные объекты читаются через атрибуты (relationship)."""
    topic = TopicRepository(session).create(name="SQL")
    question = make_question(QuestionRepository(session), topic)

    assert question.topic.name == "SQL"
    assert topic.questions == [question]


def test_search_by_text_ignores_case(session):
    """Поиск по тексту не зависит от регистра, и в русских словах тоже."""
    topic = TopicRepository(session).create(name="SQL")
    repo = QuestionRepository(session)
    make_question(repo, topic, text="Что такое Запрос?")
    make_question(repo, topic, text="Что такое таблица?")

    found = repo.search(text="запрос")

    assert [q.text for q in found] == ["Что такое Запрос?"]


def test_search_filters(session):
    """Фильтры по сложности и теме работают вместе."""
    topics = TopicRepository(session)
    sql = topics.create(name="SQL")
    python = topics.create(name="Python")
    repo = QuestionRepository(session)
    make_question(repo, sql, difficulty=1)
    wanted = make_question(repo, sql, difficulty=2)
    make_question(repo, python, difficulty=2)

    found = repo.search(difficulty=2, topic_id=sql.id)

    assert found == [wanted]


def test_add_tag_search_by_tag_and_remove_tag(session):
    """Тег привязывается к вопросу, по нему ищется и отвязывается."""
    topic = TopicRepository(session).create(name="SQL")
    tag = TagRepository(session).create(name="запрос")
    repo = QuestionRepository(session)
    tagged = make_question(repo, topic)
    make_question(repo, topic, text="Без тега")

    repo.add_tag(tagged, tag)
    assert repo.search(tag_id=tag.id) == [tagged]
    assert tag.questions == [tagged]

    repo.remove_tag(tagged, tag)
    assert repo.search(tag_id=tag.id) == []
