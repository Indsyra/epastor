from pathlib import Path
from random import random
from time import time

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
MAX_VIDEOS_PER_RUN = 20

def fetch_transcripts_for_pastor(session, pastor_id: str) -> None:
    """
    Fetch and parse the transcript segments for a given pastor's videos.

    Args:
        session: The SQLAlchemy session.
        pastor_id (str): The ID of the pastor.

    Returns:
        None: This function does not return any value.

    """
    videos = get_videos_to_transcribe(session, pastor_id=pastor_id)[:MAX_VIDEOS_PER_RUN]
    TRANSCRIPTS_DIR.mkdir(parents=True, exist_ok=True)

    consecutive_blocked = 0

    for video in videos:
        segments, language, status = get_transcript_segments(video.id)

        if status == "blocked":
            consecutive_blocked += 1
            if consecutive_blocked >= MAX_CONSECUTIVE_BLOCKED:
                logger.info("%d consecutive blocked — stopping.", MAX_CONSECUTIVE_BLOCKED)
                break
            logger.info("Sleeping for a while before retrying...")
            time.sleep(random.uniform(60,120))
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
        time.sleep(random.uniform(15,45))

if __name__ == "__main__":
    from sqlalchemy import select
    from db.models import Pastor
    from db.locks import pipeline_lock, TaskAlreadyRunningError

    with SessionLocal() as session:
        pastor = session.scalars(select(Pastor).where(Pastor.display_name == "Mohammed Sanogo")).first()
        try:
            with pipeline_lock(session, pastor.id, "fetch_transcripts"):
                fetch_transcripts_for_pastor(session, pastor_id=pastor.id)
        except TaskAlreadyRunningError as e:
            logger.warning(str(e))