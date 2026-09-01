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

class PrayerSignalStatusEnum(str, enum.Enum):
    NEW = "new"
    PRAYED = "prayed"

class HumanContactRequestCategoryEnum(str, enum.Enum):
    EMOTIONAL_SPIRITUAL = "emotional_spiritual"
    HOUSING = "housing"
    FINANCIAL = "financial"
    ADMINISTRATIVE = "administrative"
    OTHER = "other"

class ContactMethodEnum(str, enum.Enum):
    EMAIL = "email"
    PHONE = "phone"
    IN_PERSON = "in_person"

class HumanContactRequestStatusEnum(str, enum.Enum):
    NEW = "new"
    CONTACTED = "contacted"
    CLOSED = "closed"

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

class Show(Base):
    __tablename__ = "shows"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    channel_id: Mapped[str] = mapped_column(ForeignKey("channels.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    keywords: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

class Video(Base):
    __tablename__ = "videos"

    id: Mapped[str] = mapped_column(String(11), primary_key=True)
    channel_id: Mapped[str] = mapped_column(ForeignKey("channels.id"), nullable=False)
    pastor_id: Mapped[str] = mapped_column(ForeignKey("pastors.id"), nullable=False)
    show_id: Mapped[str | None] = mapped_column(ForeignKey("shows.id"), nullable=True)
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

class PrayerSignal(Base):
    __tablename__ = "prayer_signals"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    pastor_id: Mapped[str] = mapped_column(ForeignKey("pastors.id"), nullable=False)
    first_name: Mapped[str | None] = mapped_column(String(255), nullable=True, default=None)
    note: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
    status: Mapped[PrayerSignalStatusEnum] = mapped_column(Enum(PrayerSignalStatusEnum), nullable=False, default=PrayerSignalStatusEnum.NEW)

class HumanContactRequest(Base):
    __tablename__ = "human_contact_requests"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    pastor_id: Mapped[str] = mapped_column(ForeignKey("pastors.id"), nullable=False)
    first_name: Mapped[str | None] = mapped_column(String(255), nullable=True, default=None)
    category: Mapped[HumanContactRequestCategoryEnum] = mapped_column(Enum(HumanContactRequestCategoryEnum), nullable=False)
    contact_method: Mapped[ContactMethodEnum] = mapped_column(Enum(ContactMethodEnum), nullable=False)
    contact_value: Mapped[str | None] = mapped_column(String(255), nullable=True, default=None)
    note: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
    status: Mapped[HumanContactRequestStatusEnum] = mapped_column(Enum(HumanContactRequestStatusEnum), nullable=False, default=HumanContactRequestStatusEnum.NEW)
