from redis.asyncio import Redis

r = Redis.from_url("redis://localhost:6379", decode_responses=True)