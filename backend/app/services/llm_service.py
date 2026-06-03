from google import genai
from groq import Groq
from openai import OpenAI

from app.core.config import settings


class LLMService:

    def __init__(self):

        self.gemini_client = genai.Client(
            api_key=settings.GEMINI_API_KEY
        )

        self.groq_client = Groq(
            api_key=settings.GROQ_API_KEY
        )

        self.openai_client = OpenAI(
            api_key=settings.OPENAI_API_KEY
        )

        self.openrouter_client = OpenAI(
            api_key=settings.OPENROUTER_API_KEY,
            base_url="https://openrouter.ai/api/v1"
        )

    def generate(
        self,
        prompt: str
    ):

        providers = [
            "gemini",
            "groq",
            "openrouter",
            "openai"
        ]

        for provider in providers:

            try:

                if provider == "gemini":

                    response = (
                        self.gemini_client.models.generate_content(
                            model="gemini-2.0-flash",
                            contents=prompt
                        )
                    )

                    print("Using Gemini")

                    return response.text

                elif provider == "groq":

                    response = (
                        self.groq_client.chat.completions.create(
                            model="llama-3.3-70b-versatile",
                            messages=[
                                {
                                    "role": "user",
                                    "content": prompt
                                }
                            ]
                        )
                    )

                    print("Using Groq")

                    return (
                        response.choices[0]
                        .message.content
                    )

                elif provider == "openrouter":

                    response = (
                        self.openrouter_client.chat.completions.create(
                            model="meta-llama/llama-3.3-70b-instruct",
                            messages=[
                                {
                                    "role": "user",
                                    "content": prompt
                                }
                            ]
                        )
                    )

                    print("Using OpenRouter")

                    return (
                        response.choices[0]
                        .message.content
                    )

                elif provider == "openai":

                    response = (
                        self.openai_client.chat.completions.create(
                            model="gpt-4o-mini",
                            messages=[
                                {
                                    "role": "user",
                                    "content": prompt
                                }
                            ]
                        )
                    )

                    print("Using OpenAI")

                    return (
                        response.choices[0]
                        .message.content
                    )

            except Exception as e:

                print(
                    f"{provider} failed:",
                    e
                )

                continue

        return "All LLM providers are unavailable."
