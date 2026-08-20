"""
Tests du modèle Book.
Reprend : synopsis optionnel.
"""
from db.models import Pastor, Book


def _make_pastor(session):
    p = Pastor(display_name="Mohammed Sanogo")
    session.add(p)
    session.commit()
    return p.id


def test_book_synopsis_is_optional(session):
    pastor_id = _make_pastor(session)

    b = Book(
        pastor_id=pastor_id,
        title="12 portes d'influence",
        url="https://www.sanogobooks.com/products/12-portes",
        price="€16,00",
    )
    session.add(b)
    session.commit()

    assert b.synopsis is None


def test_book_stores_all_fields(session):
    pastor_id = _make_pastor(session)

    b = Book(
        pastor_id=pastor_id,
        title="12 portes d'influence",
        url="https://www.sanogobooks.com/products/12-portes",
        price="€16,00",
        synopsis="Un livre sur le leadership chrétien.",
    )
    session.add(b)
    session.commit()

    assert b.title == "12 portes d'influence"
    assert b.price == "€16,00"
    assert b.synopsis == "Un livre sur le leadership chrétien."
