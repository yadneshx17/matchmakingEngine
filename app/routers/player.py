from fastapi import APIRouter
from app.utils.redis_manager import r
import uuid, time

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

    message = {
        "message": "You have been queued",
        "player_id": playerId
    }

    print(message)
    return message