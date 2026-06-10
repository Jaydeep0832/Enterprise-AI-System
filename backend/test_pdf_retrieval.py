from app.rag.retriever import Retriever

retriever = Retriever()

results = retriever.search(
    "What is MCP?"
)

for row in results:
    print(row.content)
print("-"*80)

