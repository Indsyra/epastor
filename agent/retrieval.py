import numpy as np
from db.models import TranscriptChunk
from ingestion.embeddings import embed_texts
from ingestion.vector_store import load_or_create_index
from sqlalchemy import select

def search_chunks(session, pastor_id: str, query: str, k: int=5) -> list[TranscriptChunk]:
    query_embedding = np.array(embed_texts([query]), dtype=np.float32)
    index, chunks_ids = load_or_create_index(pastor_id)
    _, indices = index.search(query_embedding, k=k)
    mapped_ids = [chunks_ids[i] for i in indices[0]]
    results = session.scalars(
        select(TranscriptChunk).where(TranscriptChunk.id.in_(mapped_ids))
    ).all()
    results_by_id = {chunk.id: chunk for chunk in results}
    return [results_by_id[i] for i in mapped_ids if i in results_by_id]