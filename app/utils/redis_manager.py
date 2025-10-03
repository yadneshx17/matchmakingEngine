from redis.asyncio import Redis

# if not decode_response, by default its "False" 
# Requires -> decode("utf-8") while retrieval 
r = Redis.from_url("redis://localhost:6379", decode_responses=True) 