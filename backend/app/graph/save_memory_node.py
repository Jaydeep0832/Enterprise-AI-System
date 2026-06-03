from app.memory.conversation_memory import ConversationMemory

memory = ConversationMemory()


def save_memory_node(state):

    memory.add_message(
        f"Q: {state['query']}"
    )

    memory.add_message(
        f"A: {state['result']}"
    )

    return state
