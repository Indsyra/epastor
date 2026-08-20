"""
Tests du modèle Video.
Reprend : id = id YouTube (pas un UUID auto-généré), transcript_status
par défaut, show_id optionnel et sa contrainte FK.
"""
from sqlalchemy.exc import IntegrityError
import pytest

from db.models import Pastor, Channel, Show, Video, TranscriptStatusEnum


def _make_pastor_and_channel(session):
    p = Pastor(display_name="Mohammed Sanogo")
    session.add(p)
    session.commit()

    c = Channel(pastor_id=p.id, youtube_url="https://youtube.com/@test")
    session.add(c)
    session.commit()

    return p.id, c.id


def test_video_id_is_the_youtube_id_not_generated(session):
    pastor_id, channel_id = _make_pastor_and_channel(session)

    v = Video(
        id="dQw4w9WgXcQ", channel_id=channel_id, pastor_id=pastor_id,
        title="Prédication", url="https://youtube.com/watch?v=dQw4w9WgXcQ",
    )
    session.add(v)
    session.commit()

    assert v.id == "dQw4w9WgXcQ"  # pas un UUID généré


def test_video_transcript_status_defaults_to_pending(session):
    pastor_id, channel_id = _make_pastor_and_channel(session)

    v = Video(
        id="dQw4w9WgXcQ", channel_id=channel_id, pastor_id=pastor_id,
        title="Prédication", url="https://youtube.com/watch?v=dQw4w9WgXcQ",
    )
    session.add(v)
    session.commit()

    assert v.transcript_status == TranscriptStatusEnum.PENDING


def test_video_show_id_is_optional(session):
    pastor_id, channel_id = _make_pastor_and_channel(session)

    v = Video(
        id="dQw4w9WgXcQ", channel_id=channel_id, pastor_id=pastor_id,
        title="Prédication", url="https://youtube.com/watch?v=dQw4w9WgXcQ",
    )
    session.add(v)
    session.commit()

    assert v.show_id is None


def test_video_show_id_links_to_existing_show(session):
    pastor_id, channel_id = _make_pastor_and_channel(session)

    show = Show(channel_id=channel_id, name="Flamme matinale", keywords=["flamme matinale"])
    session.add(show)
    session.commit()

    v = Video(
        id="dQw4w9WgXcQ", channel_id=channel_id, pastor_id=pastor_id, show_id=show.id,
        title="Flamme matinale - Episode 12", url="https://youtube.com/watch?v=dQw4w9WgXcQ",
    )
    session.add(v)
    session.commit()

    assert v.show_id == show.id


def test_video_rejects_nonexistent_show_id(session):
    pastor_id, channel_id = _make_pastor_and_channel(session)

    v = Video(
        id="dQw4w9WgXcQ", channel_id=channel_id, pastor_id=pastor_id, show_id="id-inexistant",
        title="Prédication", url="https://youtube.com/watch?v=dQw4w9WgXcQ",
    )
    session.add(v)

    with pytest.raises(IntegrityError):
        session.commit()
