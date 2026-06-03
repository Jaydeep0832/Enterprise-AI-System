from app.services.providers import LLMProvider


class ProviderManager:

    def __init__(self):

        self.providers = [
            LLMProvider.OPENROUTER,
            LLMProvider.GROQ,
            LLMProvider.GEMINI,
            LLMProvider.OPENAI
        ]

    def get_providers(self):
        return self.providers
