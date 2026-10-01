# clear_locks.py
import sys
from db.session import SessionLocal
from db.models import PipelineLock
from sqlalchemy import delete, select

with SessionLocal() as session:
    if len(sys.argv) > 1:
        task_name = sys.argv[1]
        result = session.execute(delete(PipelineLock).where(PipelineLock.task_name == task_name))
    else:
        existing = session.scalars(select(PipelineLock)).all()
        for lock in existing:
            print(f"{lock.task_name} | pasteur {lock.pastor_id} | depuis {lock.started_at}")
        print("\nAucun verrou supprimé. Lance avec un nom de tâche pour en supprimer un :")
        print("  python clear_locks.py chunk_and_embed")
        sys.exit(0)

    session.commit()
    print(f"{result.rowcount} verrou(s) supprimé(s) pour '{task_name}'")