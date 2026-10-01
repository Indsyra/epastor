# check_orphan_vectors.py
from db.session import SessionLocal
from db.models import Pastor, TranscriptChunk
from ingestion.vector_store import load_or_create_index
from sqlalchemy import select

with SessionLocal() as session:
    pastor = session.scalars(select(Pastor).where(Pastor.display_name == "Mohammed Sanogo")).first()

    db_ids = set(session.scalars(select(TranscriptChunk.id).where(TranscriptChunk.pastor_id == pastor.id)))
    index, faiss_ids = load_or_create_index(pastor.id)

    orphans = [cid for cid in faiss_ids if cid not in db_ids]
    print(f"chunk_ids dans FAISS mais absents de la base : {len(orphans)}")

    # Les doublons éventuels dans la liste FAISS elle-même (positions multiples pour un même id)
    from collections import Counter
    counts = Counter(faiss_ids)
    dup_ids = [cid for cid, n in counts.items() if n > 1]
    print(f"chunk_ids apparaissant plusieurs fois dans l'index : {len(dup_ids)}")