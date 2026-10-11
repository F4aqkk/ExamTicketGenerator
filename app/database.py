"""Подключение к базе данных SQLite."""

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker

from app.models.base import Base
from app.paths import data_path

# Файл базы: в папке проекта, а у собранной программы рядом с exe.
DATABASE_URL = "sqlite:///" + data_path("exam_tickets.db").as_posix()


engine = create_engine(DATABASE_URL)


def enable_foreign_keys(dbapi_connection, connection_record):
    """Включает проверку внешних ключей в SQLite."""
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


def watch_foreign_keys(any_engine: Engine) -> None:
    """Включать внешние ключи при каждом подключении к этой базе."""
    event.listen(any_engine, "connect", enable_foreign_keys)


watch_foreign_keys(engine)


SessionLocal = sessionmaker(bind=engine)


def init_db():
    """Создаёт в базе все таблицы, если их ещё нет."""
    import app.models  # noqa: F401  (подключаем все модели)

    Base.metadata.create_all(engine)
