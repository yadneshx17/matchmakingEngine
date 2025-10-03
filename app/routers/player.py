from fastapi import APIRouter
from app.utils.redis_manager import r
import uuid, time, json

router = APIRouter()

# Player Service 
@router.post("/join_queue")
async def join_queue(player_name: str, player_skill: int):

    playerId = str(uuid.uuid4())

    # Add player to active players set
    await r.sadd("players", playerId)

    # Store player metadata 
    await r.hset(f"player:{playerId}", mapping={
        "name": player_name,
        "skill": player_skill,
        "joinedAt": str(time.time()),
        "status": "queued"
    })

    # add player to matchmaking queue
    await r.zadd("queue", {playerId: player_skill})

    # auto expire player after 5 min to avoid stale entries
    await r.expire(f"player:{playerId}", 600)

    # Publish event to notify matchmaking worker
    await r.publish("matchmaking-events", json.dumps({
        "event": "player_queued",
        "name": player_name,
        "playerId": playerId,
        "skill": player_skill,
        "status": "queued"
    }))

    return {
        "message": "You have been queued",
        "player_id": playerId,
        "player_name": player_name,
        "player_skill": player_skill,
        "status": "queued"
    }