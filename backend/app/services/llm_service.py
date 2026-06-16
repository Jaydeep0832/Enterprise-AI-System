import time

from google import genai
from groq import Groq
from openai import OpenAI

from app.core.config import settings
from app.core.tracing import record_llm_call

try:
    from langsmith import wrappers, traceable
    HAS_LANGSMITH = True
except ImportError:
    HAS_LANGSMITH = False
    def traceable(*args, **kwargs):
        """No-op decorator when LangSmith is not installed."""
        def decorator(func):
            return func
        if args and callable(args[0]):
            return args[0]
        return decorator

# Model name lookup for tracing
MODEL_MAP = {
    "gemini": "gemini-2.0-flash",
    "groq": "llama-3.3-70b-versatile",
    "openrouter": "meta-llama/llama-3.3-70b-instruct",
    "openai": "gpt-4o-mini",
}


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
        if HAS_LANGSMITH and settings.LANGCHAIN_API_KEY:
            self.openai_client = wrappers.wrap_openai(self.openai_client)
            self.openrouter_client = wrappers.wrap_openai(self.openrouter_client)

    @traceable(name="LLMService.generate", run_type="llm")
    def generate(self, prompt: str) -> str:
        """Try each provider in order until one succeeds."""

        for provider in ["openai", "groq", "gemini", "openrouter"]:
            start_time = time.perf_counter()
            model = MODEL_MAP.get(provider, "unknown")
            try:
                result = self._call_provider(provider, prompt)
                latency = (time.perf_counter() - start_time) * 1000
                record_llm_call(
                    provider=provider, model=model, prompt=prompt,
                    response=result, latency_ms=latency, success=True,
                )
                return result
            except Exception as e:
                latency = (time.perf_counter() - start_time) * 1000
                record_llm_call(
                    provider=provider, model=model, prompt=prompt,
                    response="", latency_ms=latency, success=False, error=str(e),
                )
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
