from fastapi import APIRouter, HTTPException
from app.utils.redis_manager import r
import uuid, time, json
from app.models.ticket import Player, Matchmaking
from typing import Dict

router = APIRouter()

# Data
latencyData = {
  "in-central": 30,
  "us-east": 180,
  "eu-west": 120,
  "asia-se": 80
}

# Player Service 
@router.post("/join_queue")
async def join_queue(gameMode: str, player_data: Player):

    playerId = str(uuid.uuid4())
    ticketId = str(uuid.uuid4()) 

    try: 
        ticket = Matchmaking(
            ticket=ticketId,
            players=[player_data],
            gameMode=gameMode,
            regionPreference=player_data.regionPreference,
            latencyData=latencyData,
            creationTime=time.time(),
            status="searching"
        )
        # print(f"Ticket: {ticket}")
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid ticket data: {e}")

    average_skill = sum(p.skill for p in ticket.players) / len(ticket.players)

    # store full ticket 
    await r.hset(f"ticket:{ticketId}", mapping={"ticketData": ticket.model_dump_json()})

    # Add the ticket to the searchable Player Pool (a Redis Sorted Set).
    # The score is the party's average skill, enabling fast searches.
    await r.zadd(f"pool:{gameMode}", {ticketId: average_skill})

    # Publish Dashboard Event
    await r.publish("dashboard_events", json.dumps({
        "event":"pool_updated",
        "gameMode": gameMode
    }))
    
    # print(f"INFO: Ticket [ {ticketId} ] for mode '{gameMode}' queued for {len(ticket.players)} player(s).")
    
    return {"message": "Ticket created and successfully queued", "ticket": ticket.model_dump()}