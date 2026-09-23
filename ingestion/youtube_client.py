from urllib.parse import urlparse, urlunparse
import yt_dlp

TARGET_TABS = ["videos", "streams"]

def build_tab_url(channel_url: str, tab: str) -> str:
    parsed = urlparse(channel_url)
    clean_path = parsed.path.rstrip("/") + f"/{tab}"
    return urlunparse((parsed.scheme, parsed.netloc, clean_path, "", "", ""))

def list_channel_videos(channel_url: str, target_tabs: list[str], max_items: int | None = None) -> list[dict]:
    """
    List all videos from a YouTube channel without downloading the content.

    Args:
        channel_url (str): The URL of the YouTube channel.
        target_tabs (list[str]): A list of target tabs to fetch videos from (e.g., ["videos", "streams"]).
        max_items (int | None): If set, only the `max_items` most recent
            videos of each tab are listed (incremental scan).
            If None, the whole tab is listed (full scan).

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
    if max_items is not None and max_items > 0:
        ydl_opts["playlistend"] = max_items

    all_videos = []
    seen_ids = set()

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