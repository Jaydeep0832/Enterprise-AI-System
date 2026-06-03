from app.rag.embedder import Embedder

embedder = Embedder()

vector = embedder.embed(
    "Vector databases are useful for RAG."
)

print(type(vector))
print(len(vector))
print(vector[:10])
