from app.repositories.topic_repository import TopicRepository


def test_create_topic(session):
    """Тема создаётся и получает id и название."""
    repo = TopicRepository(session)

    topic = repo.create(name="SQL")

    assert topic.id is not None
    assert topic.name == "SQL"


def test_get_by_name_finds_topic(session):
    """Созданную тему можно найти по названию."""
    repo = TopicRepository(session)
    repo.create(name="SQL")

    found = repo.get_by_name("SQL")

    assert found is not None
    assert found.name == "SQL"


def test_get_by_name_returns_none_if_missing(session):
    """Если темы с таким названием нет, возвращается None."""
    repo = TopicRepository(session)

    assert repo.get_by_name("Такой темы нет") is None


def test_update_topic(session):
    """Название темы можно изменить, и оно сохраняется в базе."""
    repo = TopicRepository(session)
    topic = repo.create(name="SQL")

    repo.update(topic, name="Python")

    assert repo.get_by_id(topic.id).name == "Python"


def test_delete_topic(session):
    """Удалённая тема пропадает из списка всех тем."""
    repo = TopicRepository(session)
    topic = repo.create(name="SQL")

    repo.delete(topic)

    assert repo.get_all() == []
    