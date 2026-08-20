"""
Tests du modèle TranscriptChunk.
Reprend : stockage du texte long, timestamps flottants.
"""
from db.models import Pastor, Channel, Video, TranscriptChunk


def _make_video(session):
    p = Pastor(display_name="Mohammed Sanogo")
    session.add(p)
    session.commit()

    c = Channel(pastor_id=p.id, youtube_url="https://youtube.com/@test")
    session.add(c)
    session.commit()

    v = Video(
        id="dQw4w9WgXcQ", channel_id=c.id, pastor_id=p.id,
        title="Prédication", url="https://youtube.com/watch?v=dQw4w9WgXcQ",
    )
    session.add(v)
    session.commit()

    return p.id, v.id


def test_transcript_chunk_stores_text_and_timestamps(session):
    pastor_id, video_id = _make_video(session)

    chunk = TranscriptChunk(
        video_id=video_id, pastor_id=pastor_id,
        text="La foi vient de ce qu'on entend.",
        start_seconds=125.5, end_seconds=158.2,
    )
    session.add(chunk)
    session.commit()
    chunk_id = chunk.id

    session.expire_all()
    fetched = session.get(TranscriptChunk, chunk_id)

    assert fetched.text == "La foi vient de ce qu'on entend."
    assert fetched.start_seconds == 125.5
    assert fetched.end_seconds == 158.2
