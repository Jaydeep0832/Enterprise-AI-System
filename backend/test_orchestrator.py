from app.graph.orchestrator import Orchestrator

orchestrator = Orchestrator()

queries = [
    "10 + 20",
    "What is Redis?",
    "Explain vector databases"
]

for q in queries:

    print("\nQUERY:")
    print(q)

    print("\nRESULT:")
    print(
        orchestrator.run(q)
    )

    print("\n" + "=" * 60)
