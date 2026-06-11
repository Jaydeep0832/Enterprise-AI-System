import json
from app.db.redis_client import redis_client

class LongTermMemory:
    """Stores user preferences and facts across sessions using Redis Hashes."""
    def __init__(self, user_id: str = "default_user"):
        self.user_id = user_id
        self.key = f"long_term_memory:{self.user_id}"

    def save_preference(self, key: str, value: str):
        """Save a specific user preference."""
        redis_client.hset(self.key, key, value)

    def get_preferences(self) -> dict:
        """Get all long-term preferences for the user."""
        prefs = redis_client.hgetall(self.key)
        return {k: v for k, v in prefs.items()}

    def get_context_string(self) -> str:
        prefs = self.get_preferences()
        if not prefs:
            return ""
        
        context = "User Preferences & Facts:\n"
        for k, v in prefs.items():
            context += f"- {k}: {v}\n"
        return context
