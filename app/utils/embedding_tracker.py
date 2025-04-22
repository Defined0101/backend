# app/utils/embedding_tracker.py

import redis

redis_client = redis.Redis(host="redis", port=6379, db=0)

def mark_user_for_update(user_id: int):
    redis_client.sadd("users_to_update", user_id)

def get_users_to_update() -> list[int]:
    users = redis_client.smembers("users_to_update")
    return [int(uid) for uid in users]

def clear_user_from_update(user_id: int):
    redis_client.srem("users_to_update", user_id)
