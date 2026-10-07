from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker


from app.models.base import Base

DATABASE_URL = "sqlite:///exam_tickets.db"


engine = create_engine(DATABASE_URL)


@event.listens_for(engine, "connect")
def enable_foreign_keys(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


SessionLocal = sessionmaker(bind=engine)


def init_db():
    from app.models import (  # noqa: F401
        generation,
        question,
        question_tag,
        tag,
        ticket_question,
        ticket,
        topic,
    )

    Base.metadata.create_all(engine)
