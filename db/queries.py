from sqlalchemy import select
from db.models import Channel

def get_channels_for_pastor(session, pastor_id):
    return session.scalars(select(Channel).where(Channel.pastor_id == pastor_id)).all()