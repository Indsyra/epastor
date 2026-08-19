import uuid
from sqlalchemy import JSON, Float, ForeignKey, String, Boolean, DateTime, Enum, Text, func, Integer
import enum
from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column
from db.base import Base


class StatusEnum(str, enum.Enum):
    PENDING = "pending"
    ACTIVE = "active"
    SUSPENDED = "suspended"

class TranscriptStatusEnum(str, enum.Enum):
    PENDING = "pending"
    FETCHED = "fetched"
    UNAVAILABLE = "unavailable"
    ERROR = "error"

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

class Video(Base):
    __tablename__ = "videos"

    id: Mapped[str] = mapped_column(String(11), primary_key=True)
    channel_id: Mapped[str] = mapped_column(ForeignKey("channels.id"), nullable=False)
    pastor_id: Mapped[str] = mapped_column(ForeignKey("pastors.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    url: Mapped[str] = mapped_column(String(2083), nullable=False)
    duration_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    upload_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    speaker_match: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    match_reason: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    transcript_status: Mapped[TranscriptStatusEnum] = mapped_column(Enum(TranscriptStatusEnum, create_constraint=True), nullable=False, default=TranscriptStatusEnum.PENDING)

class TranscriptChunk(Base):
    __tablename__ = "transcript_chunks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    video_id: Mapped[str] = mapped_column(ForeignKey("videos.id"), nullable=False)
    pastor_id: Mapped[str] = mapped_column(ForeignKey("pastors.id"), nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    start_seconds: Mapped[float] = mapped_column(Float, nullable=False)
    end_seconds: Mapped[float] = mapped_column(Float, nullable=False)

class Book(Base):
    __tablename__ = "books"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    pastor_id: Mapped[str] = mapped_column(ForeignKey("pastors.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    url: Mapped[str] = mapped_column(String(2083), nullable=False)
    price: Mapped[str] = mapped_column(String(50), nullable=False)
    synopsis: Mapped[str | None] = mapped_column(Text, nullable=True)

class Visitor(Base):
    __tablename__ = "visitors"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())

class VisitorPastorFollow(Base):
    __tablename__ = "visitor_pastor_follows"

    visitor_id: Mapped[str] = mapped_column(ForeignKey("visitors.id"), primary_key=True, nullable=False)
    pastor_id: Mapped[str] = mapped_column(ForeignKey("pastors.id"), primary_key=True, nullable=False)
    is_explicit_preference: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())