from app.agents.router_agent import RouterAgent

router = RouterAgent()

queries = [
    "10 + 5",
    "What is Redis?",
    "Explain vector databases"
]

for query in queries:

    print("\nQUERY:")
    print(query)

    print("\nANSWER:")
    print(
        router.route(query)
    )

    print("\n" + "=" * 60)
