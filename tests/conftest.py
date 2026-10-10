"""Общие настройки для тестов."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

import app.models  # noqa: F401  (подключаем все модели)
from app.database import watch_foreign_keys
from app.models.base import Base


@pytest.fixture
def session():
    """Пустая база в памяти для каждого теста."""
    engine = create_engine("sqlite:///:memory:")
    watch_foreign_keys(engine)  # как в настоящей базе
    Base.metadata.create_all(engine)
    with Session(engine) as db_session:
        yield db_session
    engine.dispose()  # закрыть соединение с базой после теста
