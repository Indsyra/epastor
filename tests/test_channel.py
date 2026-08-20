"""
Tests du modèle Channel.
Reprend : liaison FK à Pastor, round-trip JSON pour name_keywords,
rejet d'un pastor_id inexistant.
"""
from sqlalchemy.exc import IntegrityError
import pytest

from db.models import Pastor, Channel


def _make_pastor(session):
    p = Pastor(display_name="Mohammed Sanogo")
    session.add(p)
    session.commit()
    return p.id


def test_channel_linked_to_pastor(session):
    pastor_id = _make_pastor(session)

    c = Channel(pastor_id=pastor_id, youtube_url="https://youtube.com/@test")
    session.add(c)
    session.commit()

    assert c.pastor_id == pastor_id


def test_channel_name_keywords_roundtrip_as_list(session):
    pastor_id = _make_pastor(session)

    c = Channel(
        pastor_id=pastor_id,
        youtube_url="https://youtube.com/@test",
        name_keywords=["sanogo", "apôtre sanogo"],
    )
    session.add(c)
    session.commit()
    channel_id = c.id

    session.expire_all()  # force une vraie relecture depuis la base
    fetched = session.get(Channel, channel_id)

    assert fetched.name_keywords == ["sanogo", "apôtre sanogo"]
    assert isinstance(fetched.name_keywords, list)


def test_channel_rejects_nonexistent_pastor(session):
    c = Channel(pastor_id="id-inexistant", youtube_url="https://youtube.com/@test")
    session.add(c)

    with pytest.raises(IntegrityError):
        session.commit()
