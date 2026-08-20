"""
Tests des modèles Visitor et VisitorPastorFollow.
Reprend : clé primaire composite, rejet d'un doublon (visitor, pastor).
"""
from sqlalchemy.exc import IntegrityError
import pytest

from db.models import Pastor, Visitor, VisitorPastorFollow


def _make_pastor_and_visitor(session):
    p = Pastor(display_name="Mohammed Sanogo")
    session.add(p)

    v = Visitor()
    session.add(v)
    session.commit()

    return p.id, v.id


def test_visitor_pastor_follow_created(session):
    pastor_id, visitor_id = _make_pastor_and_visitor(session)

    follow = VisitorPastorFollow(visitor_id=visitor_id, pastor_id=pastor_id, is_explicit_preference=True)
    session.add(follow)
    session.commit()

    assert follow.is_explicit_preference is True


def test_duplicate_visitor_pastor_pair_is_rejected(session):
    """
    La clé primaire composite (visitor_id, pastor_id) doit empêcher un
    même visiteur de suivre deux fois le même pasteur.
    """
    pastor_id, visitor_id = _make_pastor_and_visitor(session)

    session.add(VisitorPastorFollow(visitor_id=visitor_id, pastor_id=pastor_id))
    session.commit()

    duplicate = VisitorPastorFollow(visitor_id=visitor_id, pastor_id=pastor_id)
    session.add(duplicate)

    with pytest.raises(IntegrityError):
        session.commit()
