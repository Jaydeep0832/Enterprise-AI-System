from app.services.providers import LLMProvider


class ProviderManager:

    def __init__(self):

        self.providers = [
            LLMProvider.OPENAI,
            LLMProvider.GROQ,
            LLMProvider.GEMINI,
            LLMProvider.OPENROUTER
        ]

    def get_providers(self):
        return self.providers
