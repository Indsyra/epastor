from contextlib import contextmanager
from sqlalchemy.exc import IntegrityError
from db.models import PipelineLock


class TaskAlreadyRunningError(Exception):
    pass


@contextmanager
def pipeline_lock(session, pastor_id: str, task_name: str):
    lock = PipelineLock(pastor_id=pastor_id, task_name=task_name)
    session.add(lock)
    try:
        session.commit()  # commit immédiat : l'autre exécution doit VOIR le verrou tout de suite
    except IntegrityError:
        session.rollback()
        raise TaskAlreadyRunningError(f"Task '{task_name}' for pastor '{pastor_id}' is already running.")
    try:
        yield
    finally:
        session.rollback()
        session.delete(lock)
        session.commit()
        pass
