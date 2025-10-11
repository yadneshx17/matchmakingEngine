from fastapi import APIRouter, HTTPException
from app.utils.redis_manager import r
import uuid, time, json
from app.models.ticket import Player, MatchmakingTicket
from typing import Dict

router = APIRouter()

# Data - More realistic latency data based on different player locations
def get_latency_data_for_player(player_name: str) -> Dict[str, int]:
    """
    generate realistic latency data based on player name (simulating different locations)
    in real system, this would be based on actual player location/IP geolocation
    """
    import hashlib
    hash_val = int(hashlib.md5(player_name.encode()).hexdigest()[:8], 16)
    
    base_latencies = {
        "in-central": 30,
        "us-east": 180, 
        "eu-west": 120,
        "asia-se": 80
    }
    
    # Add some variation based on player "location"
    variation = (hash_val % 50) - 25  # -25 to +25ms variation
    
    return {
        region: max(10, latency + variation)  # ensures minimum 10ms
        for region, latency in base_latencies.items()
    }

# Player Service 
@router.post("/join_queue")
async def join_queue(gameMode: str, player_data: Player):
    ticketId = str(uuid.uuid4()) 

    try: 
        # Generate dynamic latency data for this player
        player_latency_data = get_latency_data_for_player(player_data.playerName)
        
        ticket = MatchmakingTicket(
            ticket=ticketId,
            players=[player_data],
            gameMode=gameMode,
            regionPreference=player_data.regionPreference,
            latencyData=player_latency_data,
            creationTime=time.time(),
            status="searching"
        )
        # print(f"Ticket: {ticket}")
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid ticket data: {e}")

    try:
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
    
    except Exception as e:
        # If Redis operations fail, try to clean up
        try:
            await r.hdel(f"ticket:{ticketId}")
            await r.zrem(f"pool:{gameMode}", ticketId)
        except:
            pass  # Ignore cleanup errors
        raise HTTPException(status_code=500, detail=f"Failed to queue player: {e}")