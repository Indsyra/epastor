import json
from pathlib import Path
import faiss
import numpy as np

VECTOR_INDEX_DIR = Path("data/vector_index")
EMBEDDINGS_DIM = 768

def _index_path(pastor_id: str) -> Path:
    return VECTOR_INDEX_DIR / f"{pastor_id}.faiss"

def _ids_path(pastor_id: str) -> Path:
    return VECTOR_INDEX_DIR / f"{pastor_id}_ids.json"

def load_or_create_index(pastor_id: str) -> tuple[faiss.Index, list[str]]:
    """
    Load FAISS index and the list of chunk_ids for the given pastor.
    If the index or the list does not exist, create them.
    """
    VECTOR_INDEX_DIR.mkdir(parents=True, exist_ok=True)
    index_path = _index_path(pastor_id)
    ids_path = _ids_path(pastor_id)

    if index_path.exists() and ids_path.exists():
        index = faiss.read_index(str(index_path))
        with open(ids_path, "r") as f:
            chunk_ids = json.load(f)
    else:
        index = faiss.IndexFlatL2(EMBEDDINGS_DIM)
        chunk_ids = []
        faiss.write_index(index, str(index_path))
        with open(ids_path, "w") as f:
            json.dump(chunk_ids, f)

    return index, chunk_ids

def add_vectors(pastor_id: str, vectors: list[list], chunk_ids: list[str]) -> None:
    index, existing_ids = load_or_create_index(pastor_id)
    index.add(np.array(vectors, dtype=np.float32))
    existing_ids.extend(chunk_ids)

    faiss.write_index(index, str(_index_path(pastor_id)))
    with open(_ids_path(pastor_id), "w") as f:
        json.dump(existing_ids, f)