from enum import Enum


class LLMProvider(str, Enum):
    GEMINI = "gemini"
    GROQ = "groq"
    OPENAI = "openai"
    OPENROUTER = "openrouter"
