class ConversationMemory:

    def __init__(self):

        if not hasattr(self, "messages"):
            self.messages = []

    def add(
        self,
        role: str,
        content: str
    ):

        self.messages.append(
            {
                "role": role,
                "content": content
            }
        )

    def get_context(self):

        return self.messages

    def clear(self):

        self.messages = []


memory = ConversationMemory()
