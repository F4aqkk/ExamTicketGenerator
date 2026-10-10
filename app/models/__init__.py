"""Модели базы данных.

Здесь импортируются все модели сразу. Так SQLAlchemy знает обо всех
таблицах и может связать их между собой через relationship.
"""

from app.models.generation import Generation
from app.models.question import Question
from app.models.question_tag import QuestionTag
from app.models.tag import Tag
from app.models.ticket import Ticket
from app.models.ticket_question import TicketQuestion
from app.models.topic import Topic

__all__ = [
    "Generation",
    "Question",
    "QuestionTag",
    "Tag",
    "Ticket",
    "TicketQuestion",
    "Topic",
]
