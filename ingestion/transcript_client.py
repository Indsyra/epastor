from youtube_transcript_api import (
    AgeRestricted,
    NoTranscriptFound,
    RequestBlocked,
    TranscriptsDisabled,
    VideoUnavailable,
    VideoUnplayable,
    YouTubeTranscriptApi,
)
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

def get_transcript_segments(video_id: str) -> tuple[list[dict] | None, str | None, str]:
    """
    Fetch the transcript for a given YouTube video ID.

    Returns a tuple containing:
    - The raw transcript data as a list of dictionaries, or None if an error occurred.
    - The language code of the transcript, or the error message if an error occurred.
    """
    try:
        transcript = YouTubeTranscriptApi().fetch(video_id, languages=["fr", "en"])
        logger.info("Successfully fetched transcript for video_id %s", video_id)
        return transcript.to_raw_data(), transcript.language_code, "fetched"
    except (NoTranscriptFound, TranscriptsDisabled, VideoUnavailable, AgeRestricted, VideoUnplayable) as e:
        logger.error("Failed to fetch transcript for video_id %s: %s", video_id, e)
        return None, None, "unavailable"
    except RequestBlocked as e:
        logger.warning("Requête bloquée par YouTube pour %s: %s", video_id, e)
        return None, None, "blocked"
    except Exception as e:
        # Log the exception if needed
        logger.error("Failed to fetch transcript for video_id %s: %s", video_id, e)
        return None, None, "error"
