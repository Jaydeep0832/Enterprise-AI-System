from app.memory.conversation_memory import ConversationMemory

memory = ConversationMemory()


def memory_node(state):

    history = memory.get_history()

    return {
        "history": history
    }
