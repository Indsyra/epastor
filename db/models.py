import uuid
from sqlalchemy import JSON, ForeignKey, String, Boolean, DateTime, Enum, func
import enum
from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column
from db.base import Base


class StatusEnum(str, enum.Enum):
    PENDING = "pending"
    ACTIVE = "active"
    SUSPENDED = "suspended"

class Pastor(Base):
    __tablename__ = "pastors"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    church_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
    status: Mapped[StatusEnum] = mapped_column(Enum(StatusEnum, create_constraint=True), nullable=False, default=StatusEnum.PENDING)

class Channel(Base):
    __tablename__ = "channels"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    pastor_id: Mapped[str] = mapped_column(ForeignKey("pastors.id"), nullable=False)
    youtube_url: Mapped[str] = mapped_column(String(255), nullable=False)
    youtube_channel_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    requires_speaker_filter: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    name_keywords: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    last_scanned_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

