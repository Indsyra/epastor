from datetime import datetime, timezone, timedelta
from sqlalchemy import select
from db.models import Book, Channel, TranscriptChunk, Video
import random

def get_channels_for_pastor(session, pastor_id):
    return session.scalars(select(Channel).where(Channel.pastor_id == pastor_id)).all()

def get_videos_to_transcribe(session, pastor_id: str, months_back: int = 6) -> list[Video]:
    cutoff = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=30 * months_back)
    return session.scalars(
        select(Video)
        .where(Video.speaker_match == True)
        .where(Video.upload_date >= cutoff)
        .where(Video.transcript_status == "pending")
        .where(Video.pastor_id == pastor_id)
    ).all()

def get_videos_with_fetched_transcript(session, pastor_id: str, months_back: int = 3) -> list[Video]:
    cutoff = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=30 * months_back)
    return session.scalars(
        select(Video)
        .where(Video.speaker_match == True)
        .where(Video.upload_date >= cutoff)
        .where(Video.transcript_status == "fetched")
        .where(Video.pastor_id == pastor_id)
    ).all()

def upsert_book(session, pastor_id: str, book_data: dict) -> Book:
    """
    Insert or update a book record in the database.

    Args:
        session: The SQLAlchemy session.
        pastor_id (str): The ID of the pastor.
        book_data (dict): The book data to upsert.

    Returns:
        Book: The upserted book record.
    """
    existing_book = session.scalars(
        select(Book)
        .where(Book.pastor_id == pastor_id)
        .where(Book.url == book_data.get("url"))
    ).first()

    if existing_book:
        existing_book.title = book_data.get("title", existing_book.title)
        existing_book.price = book_data.get("price", existing_book.price)
        existing_book.synopsis = book_data.get("synopsis", existing_book.synopsis)
        session.add(existing_book)
        return existing_book
    else:
        new_book = Book(
            pastor_id=pastor_id,
            title=book_data.get("title"),
            price=book_data.get("price"),
            synopsis=book_data.get("synopsis"),
            url=book_data.get("url")
        )
        session.add(new_book)
        return new_book

def get_books_for_pastor(session, pastor_id: str) -> list[Book]:
    return session.scalars(select(Book).where(Book.pastor_id == pastor_id)).all()

def get_video_ids_with_chunks(session, pastor_id: str) -> list[str]:
    """Return the distinct video IDs that have at least one transcript chunk for the given pastor."""
    return session.scalars(
        select(TranscriptChunk.video_id)
        .where(TranscriptChunk.pastor_id == pastor_id)
        .distinct()
    ).all()

def get_chunk_window(session, video_id: str, window_size: int = 5) -> str:
    """
    Args:
        session: The SQLAlchemy session.
        video_id (str): The ID of the video.
        window_size (int, optional): The number of consecutive chunks to include in the window. Defaults to 5.
    
    Returns:
        str: The concatenated text of the selected chunk window.
    """
    chunks = session.scalars(
        select(TranscriptChunk)
        .where(TranscriptChunk.video_id == video_id)
        .order_by(TranscriptChunk.start_seconds)
    ).all()

    if len(chunks) <= window_size:
        selected = chunks
    else:
        start_index = random.randint(0, len(chunks) - window_size)
        selected = chunks[start_index:start_index + window_size]

    return " ".join(c.text for c in selected)