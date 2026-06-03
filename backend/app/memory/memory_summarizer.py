from app.services.llm_service import LLMService


class MemorySummarizer:

    def __init__(self):
        self.llm = LLMService()

    def summarize(
        self,
        messages: list
    ):

        text = "\n".join(
            [
                f"{m['role']}: {m['content']}"
                for m in messages
            ]
        )

        prompt = f"""
        Summarize this conversation.

        Focus on:
        - user goals
        - important decisions
        - project status

        Conversation:

        {text}
        """

        return self.llm.generate(
            prompt
        )
