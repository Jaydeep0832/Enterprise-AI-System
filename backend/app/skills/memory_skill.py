from app.skills.base_skill import BaseSkill, SkillDescriptor
from app.memory.long_term_memory import LongTermMemory

class SavePreferenceSkill(BaseSkill):
    AUTO_REGISTER = True

    descriptor = SkillDescriptor(
        name="save_preference",
        description="Save a fact or user preference to long-term memory. Use this when the user explicitly states a preference (e.g. 'call me John', 'I prefer concise answers').",
        parameters={
            "user_id": {"type": "string", "description": "The user ID or session ID prefix."},
            "key": {"type": "string", "description": "The category or key (e.g., 'name', 'verbosity_preference')."},
            "value": {"type": "string", "description": "The value to store."}
        },
        tags=["memory", "preference", "user"]
    )

    def execute(self, **kwargs) -> str:
        user_id = kwargs.get("user_id", "default_user")
        key = kwargs.get("key")
        value = kwargs.get("value")

        if not key or not value:
            return "Error: key and value are required."

        ltm = LongTermMemory(user_id)
        ltm.save_preference(key, value)
        return f"Successfully saved preference '{key}': '{value}'."
