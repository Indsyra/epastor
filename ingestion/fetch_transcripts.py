from pathlib import Path

from db.queries import get_videos_to_transcribe
from ingestion.transcript_client import get_transcript_segments
from db.models import Video, TranscriptChunk
from db.session import SessionLocal
import json
import logging

logger = logging.getLogger(__name__)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)

TRANSCRIPTS_DIR = Path("data/transcripts")
MAX_CONSECUTIVE_BLOCKED = 3

def fetch_transcripts_for_pastor(session, pastor_id: str) -> list[dict] | None:
    """
    Fetch and parse the transcript segments for a given YouTube video ID.

    Update:
    - Video transcript status and language
    - Transcript chunks in the database.
    """
    videos = get_videos_to_transcribe(session, pastor_id=pastor_id)
    TRANSCRIPTS_DIR.mkdir(parents=True, exist_ok=True)

    consecutive_blocked = 0

    for video in videos:
        segments, language, status = get_transcript_segments(video.id)

        if status == "blocked":
            consecutive_blocked += 1
            if consecutive_blocked >= MAX_CONSECUTIVE_BLOCKED:
                print(f"{MAX_CONSECUTIVE_BLOCKED} consecutive blocked — stopping.")
                break
            continue
        else:
            consecutive_blocked = 0

        if status == "fetched":
            transcript_path = TRANSCRIPTS_DIR / f"{video.id}.json"
            with open(transcript_path, "w", encoding="utf-8") as f:
                json.dump(segments, f, ensure_ascii=False, indent=4)
                logger.info("Transcript for video_id %s saved to %s", video.id, transcript_path)
            video.transcript_status = "fetched"
            video.language = language
        else:
            video.transcript_status = status
        session.add(video)
    session.commit()

if __name__ == "__main__":
    from sqlalchemy import select
    from db.models import Pastor

    with SessionLocal() as session:
        pastor = session.scalars(select(Pastor).where(Pastor.display_name == "Mohammed Sanogo")).first()
        fetch_transcripts_for_pastor(session, pastor_id=pastor.id)