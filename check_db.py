from sqlalchemy import create_engine, text

engine = create_engine("sqlite:///epastor.db")
with engine.connect() as conn:
    result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))
    print([r[0] for r in result])