from app.graph.langgraph_workflow import graph

queries = [
    "10 + 20",
    "What is Redis?",
    "Explain vector databases"
]

for query in queries:

    result = graph.invoke(
        {
            "query": query
        }
    )

    print("\nQUERY:")
    print(query)

    print("\nRESULT:")
    print(result["result"])

    print("\n" + "=" * 60)
