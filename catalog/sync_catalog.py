from catalog.shopify_scraper import fetch_shop_meta, fetch_all_products, extract_book_data
from db.models import Pastor
from db.queries import upsert_book
from sqlalchemy import select

def sync_catalog_for_pastor(session, pastor_id: str) -> int:
    """
    Synchronize the catalog for a given pastor.

    Args:
        session: The database session.
        pastor_id: The ID of the pastor whose catalog needs to be synchronized.

    Returns:
        The number of items synchronized or 0 if no shop is configured for this pastor.
    """
    pastor = session.scalars(select(Pastor).where(Pastor.id == pastor_id)).first()
    if not pastor or not pastor.book_shop_url:
        return 0

    money_format = fetch_shop_meta(pastor.book_shop_url).get("money_format")
    pastor_books = fetch_all_products(pastor.book_shop_url)

    for product in pastor_books:
        book_data = extract_book_data(product, pastor.book_shop_url, money_format)
        upsert_book(session, pastor.id, book_data)

    session.commit()
    return len(pastor_books)
