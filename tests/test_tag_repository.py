"""Тесты репозитория тегов."""

import pytest
from sqlalchemy.exc import IntegrityError

from app.repositories.tag_repository import TagRepository


def test_create_tag(session):
    """Тег создаётся и получает id и название."""
    repo = TagRepository(session)

    tag = repo.create(name="запрос")

    assert tag.id is not None
    assert tag.name == "запрос"


def test_get_by_name_finds_tag(session):
    """Созданный тег можно найти по названию."""
    repo = TagRepository(session)
    repo.create(name="запрос")

    assert repo.get_by_name("запрос") is not None


def test_get_by_name_returns_none_if_missing(session):
    """Если тега с таким названием нет, возвращается None."""
    repo = TagRepository(session)

    assert repo.get_by_name("Такого тега нет") is None


def test_tag_name_is_unique(session):
    """Два тега с одним названием создать нельзя (unique)."""
    repo = TagRepository(session)
    repo.create(name="запрос")

    with pytest.raises(IntegrityError):
        repo.create(name="запрос")


def test_update_and_delete_tag(session):
    """Тег можно переименовать и удалить."""
    repo = TagRepository(session)
    tag = repo.create(name="запрос")

    repo.update(tag, name="код")
    assert repo.get_by_id(tag.id).name == "код"

    repo.delete(tag)
    assert repo.get_all() == []
