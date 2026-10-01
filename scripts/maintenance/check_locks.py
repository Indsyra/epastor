# check_locks.py
from db.session import SessionLocal
from db.models import PipelineLock
from sqlalchemy import select

with SessionLocal() as session:
    for lock in session.scalars(select(PipelineLock)).all():
        print(f"{lock.task_name} | pasteur {lock.pastor_id} | depuis {lock.started_at}")