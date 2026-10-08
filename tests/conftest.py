"""Общие настройки для тестов."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.models.base import Base


@pytest.fixture
def session():
    """Пустая база в памяти для каждого теста."""
    from app.models import (  # noqa: F401
        generation,
        question,
        question_tag,
        tag,
        ticket,
        ticket_question,
        topic,
    )

    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as db_session:
        yield db_session
