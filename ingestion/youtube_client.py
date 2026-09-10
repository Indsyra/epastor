from urllib.parse import urlparse, urlunparse
import yt_dlp

TARGET_TABS = ["videos", "streams"]

def build_tab_url(channel_url: str, tab: str) -> str:
    parsed = urlparse(channel_url)
    clean_path = parsed.path.rstrip("/") + f"/{tab}"
    return urlunparse((parsed.scheme, parsed.netloc, clean_path, "", "", ""))

def list_channel_videos(channel_url: str, target_tabs: list[str]) -> list[dict]:
    """
    List all videos from a YouTube channel without downloading the content.

    Args:
        channel_url (str): The URL of the YouTube channel.

    Returns:
        list[dict]: A list of dictionaries containing video information.
    """

    ydl_opts = {
        "extract_flat": True,
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
        "extractor_args": {"youtubetab": {"approximate_date": [""]}},
    }

    all_videos = []

    for tab in target_tabs:
        videos_url = build_tab_url(channel_url, tab)

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            try:
                info = ydl.extract_info(videos_url, download=False)
            except Exception as e:
                print(f"Error extracting info from {videos_url}: {e}")
                continue

        entries = info.get("entries", []) if info else []
        videos = []
        seen_ids = set()
        for e in entries:
            if not e:
                continue
            video_id = e.get("id")
            if video_id in seen_ids:
                continue
            seen_ids.add(video_id)
            videos.append(
                {
                    "video_id": video_id,
                    "title": e.get("title", ""),
                    "url": f"https://www.youtube.com/watch?v={video_id}",
                    "duration": e.get("duration"),
                    "timestamp": e.get("timestamp"),
                    "source_tab": tab,
                }
            )
        all_videos.extend(videos)
    return all_videos