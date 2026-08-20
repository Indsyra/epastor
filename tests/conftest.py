"""
Configuration pytest partagée par tous les tests.

Fournit une fixture `session` : une base SQLite en mémoire, fraîche et
isolée pour chaque test (pas de fichier partagé, pas de pollution entre
tests), avec les 8 tables créées et les clés étrangères activées.
"""
import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from db.base import Base
# L'import des modèles est nécessaire pour que Base.metadata les connaisse
from db.models import (  # noqa: F401
    Pastor, Channel, Show, Video, TranscriptChunk, Book, Visitor, VisitorPastorFollow,
    StatusEnum, TranscriptStatusEnum,
)


@pytest.fixture
def session():
    engine = create_engine("sqlite:///:memory:")

    @event.listens_for(engine, "connect")
    def enable_sqlite_foreign_keys(dbapi_conn, conn_record):
        dbapi_conn.execute("PRAGMA foreign_keys=ON")

    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)

    with SessionLocal() as s:
        yield s
