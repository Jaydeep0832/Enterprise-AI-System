from app.services.llm_service import LLMService

llm = LLMService()

response = llm.generate(
    "Explain FastAPI in one sentence."
)

print(response)
