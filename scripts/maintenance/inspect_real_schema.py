# inspect_real_schema.py
from db.session import engine
from sqlalchemy import text

with engine.connect() as conn:
    result = conn.execute(text("SELECT sql FROM sqlite_master WHERE name='videos'"))
    print(result.fetchone()[0])