from app.rag.retriever import Retriever

retriever = Retriever()

queries = [
    "What is Retrieval Augmented Generation?",
    "Which database stores vectors?",
    "What is Redis?",
    "Python API framework"
]

for query in queries:
    print(f"\nQuery: {query}")

    results = retriever.search(
        query,
        limit=2
    )

    for row in results:
        print(row)
