import numpy as np
from rapidfuzz import fuzz
from db.models import TranscriptChunk, Book
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

def find_matching_book(extracted_title: str, catalog: list[Book], threshold: int = 70) -> Book | None:
    """
    Find the book in the catalog whose title most closely matches the extracted title.
    Returns None if no match exceeds the threshold.
    """
    best_match = None
    best_score = 0

    for book in catalog:
        score = fuzz.partial_ratio(extracted_title.lower(), book.title.lower())
        if score > best_score:
            best_score = score
            best_match = book

    if best_score >= threshold:
        return best_match
    return None