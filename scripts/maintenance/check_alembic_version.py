# check_alembic_version.py
from db.session import engine
from sqlalchemy import text

with engine.connect() as conn:
    result = conn.execute(text("SELECT version_num FROM alembic_version"))
    print(result.fetchone())