from app.db.redis_client import redis_client

redis_client.set("health", "ok")

value = redis_client.get("health")

print("Redis Connected:", value)
