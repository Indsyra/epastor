from datetime import datetime, timezone, timedelta
from sqlalchemy import select
from db.models import Channel, Video

def get_channels_for_pastor(session, pastor_id):
    return session.scalars(select(Channel).where(Channel.pastor_id == pastor_id)).all()

def get_videos_to_transcribe(session, pastor_id: str, months_back: int = 3) -> list[Video]:
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