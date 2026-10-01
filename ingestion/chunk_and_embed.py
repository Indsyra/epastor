import json
import logging
from pathlib import Path

from db.queries import get_chunks_for_video, get_videos_by_chunking_status
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
    # Vidéos jamais commencées : il faut tout faire
    pending_videos = get_videos_by_chunking_status(session, pastor_id, ChunkingStatusEnum.PENDING)
    # Vidéos interrompues après le commit des chunks, mais avant l'indexation FAISS
    chunked_videos = get_videos_by_chunking_status(session, pastor_id, ChunkingStatusEnum.CHUNKED)

    for video in pending_videos:
        transcript_path = TRANSCRIPTS_DIR / f"{video.id}.json"
        if not transcript_path.exists():
            logger.warning("Transcript introuvable pour %s, ignoré", video.id)
            continue

        with open(transcript_path, "r", encoding="utf-8") as f:
            segments = json.load(f)

        chunks = chunk_segments(segments)
        for chunk in chunks:
            transcript_chunk = TranscriptChunk(
                video_id=video.id,
                pastor_id=pastor_id,
                language=video.language,
                text=chunk["text"],
                start_seconds=chunk["start_seconds"],
                end_seconds=chunk["end_seconds"],
            )
            session.add(transcript_chunk)

        video.chunking_status = ChunkingStatusEnum.CHUNKED
        session.add(video)
        session.commit()  # les chunks sont maintenant définitivement en base
        chunked_videos.append(video)  # à indexer juste après, comme les autres

    for video in chunked_videos:
        existing_chunks = get_chunks_for_video(session, video.id)
        embedded_chunks = embed_texts([c.text for c in existing_chunks])
        chunk_ids_list = [c.id for c in existing_chunks]

        add_vectors(pastor_id, embedded_chunks, chunk_ids_list)

        video.chunking_status = ChunkingStatusEnum.DONE
        session.add(video)
        session.commit()
        logger.info("Vidéo %s indexée avec succès", video.id)
    
if __name__ == "__main__":
    from db.models import Pastor
    from db.locks import pipeline_lock, TaskAlreadyRunningError

    with SessionLocal() as session:
        pastor = session.scalars(select(Pastor).where(Pastor.display_name == "Mohammed Sanogo")).first()
        try:
            with pipeline_lock(session, pastor.id, "chunk_and_embed"):
                chunk_and_embed_for_pastor(session, pastor.id)
        except TaskAlreadyRunningError as e:
            logger.warning(str(e))