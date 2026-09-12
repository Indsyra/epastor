from sentence_transformers import SentenceTransformer
_model = None

def get_model():
    global _model
    if _model is None:
        _model = SentenceTransformer('paraphrase-multilingual-mpnet-base-v2')
    return _model

def embed_texts(texts: list[str]) -> list[list[float]]:
    model = get_model()
    return model.encode(texts).tolist()