from typing import Optional

from sqlalchemy.orm import DeclarativeBase, declarative_base, Mapped, mapped_column
from sqlalchemy import UniqueConstraint

from src import settings


Base = declarative_base()


class Reading(Base):
    __tablename__ = settings.READING_TABLE

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    timestamp: Mapped[Optional[float]]
    label: Mapped[Optional[str]]
    reading: Mapped[Optional[str]]
    units: Mapped[Optional[str]]

    __table_args__ = (UniqueConstraint('timestamp', 'label', name="_timestamp_label_uc"),)
