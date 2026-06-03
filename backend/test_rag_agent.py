from app.agents.rag_agent import RAGAgent

agent = RAGAgent()

questions = [
    "What is Retrieval Augmented Generation?",
    "What is Redis?",
    "What is FastAPI?"
]

for question in questions:
    print("\nQUESTION:")
    print(question)

    print("\nANSWER:")
    print(agent.ask(question))

    print("\n" + "=" * 60)
