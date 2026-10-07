"""Базовый класс для всех моделей базы данных."""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Общий родитель всех моделей. По нему создаются таблицы."""
