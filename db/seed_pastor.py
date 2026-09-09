from db.session import SessionLocal
from db.models import Pastor, Channel
from sqlalchemy import select
import uuid
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

def seed():
    with SessionLocal() as session:
        # 1. Vérifier si Sanogo existe déjà (par display_name)
        logger.info("Checking if Pastor 'Mohammed Sanogo' exists in the database...")
        pastor = session.scalars(select(Pastor).where(Pastor.display_name=="Mohammed Sanogo")).first()

        # 2. Si non : créer le Pastor
        if not pastor:
            logger.info("Pastor 'Mohammed Sanogo' does not exist. Creating...")
            pastor = Pastor(display_name="Mohammed Sanogo")
            session.add(pastor)
            session.flush()  # pour obtenir l'ID du pastor
            logger.info(f"Pastor 'Mohammed Sanogo' created with ID: {pastor.id}")

             # 3. Créer les deux Channel (perso + église) rattachés à ce pastor_id
            logger.info("Creating channels for Pastor 'Mohammed Sanogo'...")
            channel_perso = Channel(
                id=str(uuid.uuid4()),
                youtube_channel_id="UC4A20rdIi2CTwydYoMZGnAQ",
                youtube_url="https://youtube.com/@mohammedsanogo?si=64eJd95xoZ4O9Uf2",
                pastor_id=pastor.id,
                requires_speaker_filter=False,
                name_keywords=["mslive", "mieux que 1000 ailleurs", "flamme matinale", "nightfire", "priere24"],
                target_tabs=["streams"],
            )
            channel_eglise = Channel(
                id=str(uuid.uuid4()),
                youtube_channel_id="UCOBrKVhgjiUcSoGyqeo29WA",
                youtube_url="https://youtube.com/@eglisevasesdhonneur?si=zo438UIDKuTgi22z",
                pastor_id=pastor.id,
                requires_speaker_filter=True,
                name_keywords=["apôtre mohammed sanogo", "pst mohammed sanogo", "pasteur mohammed sanogo"],
                target_tabs=["streams"],
            )
            session.add_all([channel_perso, channel_eglise])
            logger.info(f"Channels created for Pastor 'Mohammed Sanogo': {channel_perso.youtube_url}, {channel_eglise.youtube_url}")
    
            # 4. session.commit()
            session.commit()
            logger.info("Database seeding completed successfully.")
        else:
            logger.info(f"Pastor 'Mohammed Sanogo' already exists with ID: {pastor.id}")
        

if __name__ == "__main__":
    seed()