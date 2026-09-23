from datetime import datetime, timezone
from db.session import SessionLocal
from sqlalchemy import select
from db.models import Pastor, Video
from db.queries import get_channels_for_pastor
from ingestion.youtube_client import list_channel_videos
from ingestion.matching import title_mentions_speaker
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

RECENT_SCAN_LIMIT = 50

def parse_upload_date(raw: str | None) -> datetime | None:
    if not raw:
        return None
    return datetime.fromtimestamp(raw, tz=timezone.utc).replace(tzinfo=None)

def discover_and_save_videos(session, pastor_id: str) -> None:
    logger.info("Starting discovery for pastor_id %s", pastor_id)
    channels = get_channels_for_pastor(session, pastor_id)
    logger.info("Found %d channels for pastor_id %s", len(channels), pastor_id)
    logger.info("Discovering videos for pastor_id %s", pastor_id)
    known_video_ids = set(session.scalars(select(Video.id).where(Video.pastor_id == pastor_id)))
    for channel in channels:
        inserted = 0
        max_items = None if channel.last_scanned_at is None else RECENT_SCAN_LIMIT
        raw_videos = list_channel_videos(channel.youtube_url, channel.target_tabs, max_items=max_items)
        if max_items is not None and not any(r["video_id"] in known_video_ids for r in raw_videos):
            logger.info("No new videos found for channel_id %s within the recent %d scan limit", channel.id, max_items)
            continue
        logger.info("Found %d videos for channel_id %s", len(raw_videos), channel.id)
        logger.info("Processing %d videos for channel_id %s", len(raw_videos), channel.id)
        for raw in raw_videos:
            video_id = raw["video_id"]
            if video_id in known_video_ids:
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
                upload_date=parse_upload_date(raw["timestamp"]),
                duration_seconds=raw["duration"],
                source_tab=raw["source_tab"],
            )
            session.add(video)
            inserted += 1
            known_video_ids.add(video_id)
        logger.info("Inserted %d new videos for channel_id %s", inserted, channel.id)
        channel.last_scanned_at = datetime.utcnow()
        session.add(channel)
        logger.info("Updated last_scanned_at for channel_id %s", channel.id)
    session.commit()

if __name__ == "__main__":
    with SessionLocal() as session:
        pastor = session.scalars(select(Pastor).where(Pastor.display_name == "Mohammed Sanogo")).first()
        discover_and_save_videos(session, pastor.id)
        print("Discovery complete")