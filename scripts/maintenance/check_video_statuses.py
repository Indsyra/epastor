# check_video_statuses.py
from db.session import SessionLocal
from db.models import Pastor, Video
from sqlalchemy import select, func

with SessionLocal() as session:
    pastor = session.scalars(select(Pastor).where(Pastor.display_name == "Mohammed Sanogo")).first()
    counts = session.execute(
        select(Video.chunking_status, func.count())
        .where(Video.pastor_id == pastor.id)
        .group_by(Video.chunking_status)
    ).all()
    for status, n in counts:
        print(f"{status}: {n}")