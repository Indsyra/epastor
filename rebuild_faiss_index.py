# rebuild_faiss_index.py
from pathlib import Path
from tqdm import tqdm
from db.session import SessionLocal
from db.models import Pastor, TranscriptChunk
from sqlalchemy import select
from ingestion.embeddings import embed_texts
from ingestion.vector_store import add_vectors, VECTOR_INDEX_DIR

BATCH_SIZE = 500

with SessionLocal() as session:
    pastor = session.scalars(select(Pastor).where(Pastor.display_name == "Mohammed Sanogo")).first()

    index_path = VECTOR_INDEX_DIR / f"{pastor.id}.faiss"
    ids_path = VECTOR_INDEX_DIR / f"{pastor.id}_ids.json"
    index_path.unlink(missing_ok=True)
    ids_path.unlink(missing_ok=True)

    chunks = session.scalars(select(TranscriptChunk).where(TranscriptChunk.pastor_id == pastor.id)).all()

    for i in tqdm(range(0, len(chunks), BATCH_SIZE), desc="Ré-indexation FAISS"):
        batch = chunks[i:i + BATCH_SIZE]
        texts = [c.text for c in batch]
        chunk_ids = [c.id for c in batch]
        vectors = embed_texts(texts)
        add_vectors(pastor.id, vectors, chunk_ids)

    print(f"Index reconstruit avec {len(chunks)} chunks uniques")