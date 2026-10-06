from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Topic(Base):
    __tablename__ = "topics"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(unique=True)
