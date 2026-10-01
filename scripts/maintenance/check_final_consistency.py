# check_final_consistency.py
from db.session import SessionLocal
from db.models import Pastor, TranscriptChunk
from ingestion.vector_store import load_or_create_index
from sqlalchemy import select, func

with SessionLocal() as session:
    pastor = session.scalars(select(Pastor).where(Pastor.display_name == "Mohammed Sanogo")).first()

    total_db = session.scalar(select(func.count()).select_from(TranscriptChunk).where(TranscriptChunk.pastor_id == pastor.id))
    index, chunk_ids = load_or_create_index(pastor.id)

    print(f"Chunks en base : {total_db}")
    print(f"Vecteurs FAISS : {index.ntotal}")
    print(f"chunk_ids      : {len(chunk_ids)}")

    if total_db == index.ntotal == len(chunk_ids):
        print("✅ Cohérence parfaite")
    else:
        print("⚠️ Incohérence détectée")