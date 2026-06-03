
import json

from app.db.redis_client import redis_client


class RedisMemory:

    def __init__(
        self,
        session_id: str
    ):

        self.session_id = session_id

    def add(
        self,
        role: str,
        content: str
    ):

        item = {
            "role": role,
            "content": content
        }

        redis_client.rpush(
            self.session_id,
            json.dumps(item)
        )

    def get_context(self):

        items = redis_client.lrange(
            self.session_id,
            0,
            -1
        )

        return [
            json.loads(item)
            for item in items
        ]

    def clear(self):

        redis_client.delete(
            self.session_id
        )
