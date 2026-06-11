from google import genai
from groq import Groq
from openai import OpenAI
from langsmith import wrappers, traceable

from app.core.config import settings

class LLMService:

    def __init__(self):
        self.gemini_client = genai.Client(api_key=settings.GEMINI_API_KEY)
        self.groq_client = Groq(api_key=settings.GROQ_API_KEY)
        
        # Initialize OpenAI clients
        self.openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.openrouter_client = OpenAI(
            api_key=settings.OPENROUTER_API_KEY,
            base_url="https://openrouter.ai/api/v1",
        )

        # Wrap with LangSmith if configured
        if settings.LANGCHAIN_API_KEY:
            self.openai_client = wrappers.wrap_openai(self.openai_client)
            self.openrouter_client = wrappers.wrap_openai(self.openrouter_client)

    def generate(self, prompt: str) -> str:
        """Try each provider in order until one succeeds."""

        for provider in ["gemini", "groq", "openrouter", "openai"]:
            try:
                return self._call_provider(provider, prompt)
            except Exception as e:
                print(f"{provider} failed: {e}")
                continue

        return "All LLM providers are currently unavailable."

    def _call_provider(self, provider: str, prompt: str) -> str:
        if provider == "gemini":
            response = self.gemini_client.models.generate_content(
                model="gemini-2.0-flash",
                contents=prompt,
            )
            return response.text

        # groq, openrouter, openai all use the openai-compatible format
        client_map = {
            "groq": (self.groq_client, "llama-3.3-70b-versatile"),
            "openrouter": (self.openrouter_client, "meta-llama/llama-3.3-70b-instruct"),
            "openai": (self.openai_client, "gpt-4o-mini"),
        }

        client, model = client_map[provider]
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.choices[0].message.content
