"""
Tests du modèle Show.
Reprend : is_active par défaut, liaison à une chaîne.
"""
from db.models import Pastor, Channel, Show


def _make_channel(session):
    p = Pastor(display_name="Mohammed Sanogo")
    session.add(p)
    session.commit()

    c = Channel(pastor_id=p.id, youtube_url="https://youtube.com/@test")
    session.add(c)
    session.commit()

    return c.id


def test_show_is_active_by_default(session):
    channel_id = _make_channel(session)

    show = Show(channel_id=channel_id, name="Flamme matinale", keywords=["flamme matinale"])
    session.add(show)
    session.commit()

    assert show.is_active is True


def test_show_keywords_roundtrip_as_list(session):
    channel_id = _make_channel(session)

    show = Show(channel_id=channel_id, name="Nightfire", keywords=["nightfire", "night fire"])
    session.add(show)
    session.commit()
    show_id = show.id

    session.expire_all()
    fetched = session.get(Show, show_id)

    assert fetched.keywords == ["nightfire", "night fire"]
