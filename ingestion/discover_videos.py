from datetime import datetime
from db.session import SessionLocal
from sqlalchemy import select
from db.models import Pastor, Video
from db.queries import get_channels_for_pastor
from ingestion.youtube_client import list_channel_videos
from ingestion.matching import title_mentions_speaker, parse_upload_date


def discover_and_save_videos(session, pastor_id: str) -> None:
    channels = get_channels_for_pastor(session, pastor_id)

    for channel in channels:
        raw_videos = list_channel_videos(channel.youtube_url)

        for raw in raw_videos:
            video_id = raw["video_id"]
            existing = session.get(Video, video_id)
            if existing:
                continue

            if channel.requires_speaker_filter:
                mentions, reason = title_mentions_speaker(raw["title"], channel.name_keywords)
            else:
                mentions, reason = True, "No speaker filter required (Individual channel)"

            video = Video(
                id=video_id,
                title=raw["title"],
                url=raw["url"],
                speaker_match=mentions,
                match_reason=reason,
                pastor_id=pastor_id,
                channel_id=channel.id,
                upload_date=parse_upload_date(raw["upload_date"]),
                duration_seconds=raw["duration"],
            )
            session.add(video)
        channel.last_scanned_at = datetime.utcnow()
        session.add(channel)
    session.commit()

if __name__ == "__main__":
    with SessionLocal() as session:
        pastor = session.scalars(select(Pastor).where(Pastor.display_name == "Mohammed Sanogo")).first()
        discover_and_save_videos(session, pastor.id)
        print("Discovery complete")