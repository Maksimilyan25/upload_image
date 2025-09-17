from sqlalchemy import String, Uuid, Enum, JSON
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from uuid import UUID, uuid4
from typing import Dict, Optional
import enum


class Base(DeclarativeBase):
    pass


class ImageStatus(str, enum.Enum):
    NEW = "NEW"
    PROCESSING = "PROCESSING"
    DONE = "DONE"
    ERROR = "ERROR"


class Image(Base):
    __tablename__ = "images"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    status: Mapped[ImageStatus] = mapped_column(
        Enum(ImageStatus), default=ImageStatus.NEW
    )
    original_url: Mapped[str] = mapped_column(String, nullable=False)
    thumbnails: Mapped[Optional[Dict[str, str]]] = mapped_column(
        JSON, nullable=True)
