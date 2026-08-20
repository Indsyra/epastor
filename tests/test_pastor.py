"""
Tests du modèle Pastor.
Reprend les vérifications faites manuellement : génération d'id,
valeurs par défaut, contrainte enum sur `status`.
"""
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
import pytest

from db.models import Pastor, StatusEnum


def test_pastor_id_is_auto_generated(session):
    p = Pastor(display_name="Mohammed Sanogo")
    session.add(p)
    session.commit()

    assert p.id is not None
    assert len(p.id) == 36  # format UUID


def test_pastor_church_name_is_optional(session):
    p = Pastor(display_name="Mohammed Sanogo")
    session.add(p)
    session.commit()

    assert p.church_name is None


def test_pastor_status_defaults_to_pending(session):
    p = Pastor(display_name="Mohammed Sanogo")
    session.add(p)
    session.commit()

    assert p.status == StatusEnum.PENDING


def test_pastor_status_rejects_invalid_value(session):
    """
    La contrainte CHECK générée par Enum(..., create_constraint=True)
    doit rejeter une valeur hors énumération, même en contournant l'ORM.
    """
    with pytest.raises(IntegrityError):
        session.execute(
            text(
                "INSERT INTO pastors (id, display_name, status) "
                "VALUES ('x', 'Test', 'not_a_valid_status')"
            )
        )
        session.commit()
