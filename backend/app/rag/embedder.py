from sentence_transformers import SentenceTransformer


class Embedder:
    """Singleton embedder — loads the model once and reuses across services."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.model = SentenceTransformer("all-MiniLM-L6-v2")
        return cls._instance

    def embed(self, text: str):
        return self.model.encode(text).tolist()
