def chunk_segments(
        segments: list[str],
        min_duration: float = 30.0,
        max_duration: float = 60.0,
) -> list[dict]:
    """
    Gather segments into chunks based on minimum and maximum duration.

    Args:
        segments (list[str]): List of text segments to be chunked.
        min_duration (float): Minimum duration of each chunk.
        max_duration (float): Maximum duration of each chunk.

    Returns:
        list[dict]: List of dictionaries representing the chunks with their text, start_seconds, and end_seconds.
    """
    chunks = []
    current_segments = []
    current_duration = 0.0
    chunk_start = None

    for segment in segments:
        segment_end = segment["start"] + segment["duration"]
        if chunk_start is None:
            chunk_start = segment["start"]

        if current_duration + segment["duration"] > max_duration and current_segments:
            chunks.append({
                "text": " ".join(segment["text"] for segment in current_segments),
                "start_seconds": chunk_start,
                "end_seconds": current_segments[-1]["start"] + current_segments[-1]["duration"],
            })
            current_segments = []
            current_duration = 0.0
            chunk_start = segment["start"]

        if current_duration >= min_duration and current_segments:
            chunks.append({
                "text": " ".join(segment["text"] for segment in current_segments),
                "start_seconds": chunk_start,
                "end_seconds": current_segments[-1]["start"] + current_segments[-1]["duration"],
            })
            current_segments = []
            current_duration = 0.0
            chunk_start = segment["start"]
        
        current_segments.append(segment)
        current_duration = segment_end - chunk_start

    if current_segments:
        chunks.append({
            "text": " ".join(segment["text"] for segment in current_segments),
            "start_seconds": chunk_start,
            "end_seconds": current_segments[-1]["start"] + current_segments[-1]["duration"],
        })

    return chunks