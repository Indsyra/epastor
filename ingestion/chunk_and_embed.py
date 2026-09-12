import json
import logging
from pathlib import Path

from db.queries import get_videos_with_fetched_transcript
from db.models import TranscriptStatusEnum, Video, TranscriptChunk, ChunkingStatusEnum
from db.session import SessionLocal
from ingestion.chunking import chunk_segments
from ingestion.embeddings import embed_texts
from ingestion.vector_store import add_vectors
from sqlalchemy import select

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

TRANSCRIPTS_DIR = Path("data/transcripts")

def get_videos_to_chunk(session, pastor_id: str) -> list[Video]:
    return session.scalars(
        select(Video).where(
            Video.pastor_id == pastor_id
        ).where(
            Video.transcript_status == TranscriptStatusEnum.FETCHED
        ).where(
            Video.chunking_status == ChunkingStatusEnum.PENDING
        )
    ).all()

def chunk_and_embed_for_pastor(session, pastor_id: str) -> None:
    videos = get_videos_with_fetched_transcript(session, pastor_id)

    for video in videos:
        chunk_ids_list = []
        transcript_path = TRANSCRIPTS_DIR / f"{video.id}.json"
        if not transcript_path.exists():
            logger.warning(f"Transcript for video {video.id} not found at {transcript_path}")
            continue

        with open(transcript_path, "r", encoding="utf-8") as f:
            segments = json.load(f)

        chunks = chunk_segments(segments)
        embedded_chunks = embed_texts([chunk["text"] for chunk in chunks])

        for chunk, embedded_chunk in zip(chunks, embedded_chunks):
            transcript_chunk = TranscriptChunk(
                video_id=video.id,
                pastor_id=pastor_id,
                language=video.language,
                text=chunk["text"],
                start_seconds=chunk["start_seconds"],
                end_seconds=chunk["end_seconds"],
            )
            session.add(transcript_chunk)
            session.flush()  # Ensure the transcript_chunk.id is populated before appending to chunk_ids_list
            chunk_ids_list.append(transcript_chunk.id)

        add_vectors(pastor_id, embedded_chunks, chunk_ids_list)
        video.chunking_status = ChunkingStatusEnum.DONE
        session.add(video)
        session.commit()
        logger.info(f"Finished processing video {video.id}")
    
if __name__ == "__main__":
    from db.models import Pastor
    with SessionLocal() as session:
        pastor = session.scalars(select(Pastor).where(Pastor.display_name == "Mohammed Sanogo")).first()
        chunk_and_embed_for_pastor(session, pastor.id)