from fastapi import APIRouter, HTTPException
from app.utils.redis_manager import r
import uuid, time, json
from app.models.ticket import Player, MatchmakingTicket
from typing import Dict, List

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

# API endpoints for frontend data
@router.get("/game_modes")
async def get_game_modes():
    """Get available game modes from backend configuration"""
    try:
        with open("gameModes.json", 'r') as f:
            game_modes = json.load(f)
        return {"game_modes": game_modes}
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Game modes configuration not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load game modes: {e}")

@router.get("/pool_status")
async def get_pool_status():
    """Get current pool status for all game modes"""
    try:
        with open("gameModes.json", 'r') as f:
            game_modes = json.load(f)
        
        pool_status = {}
        for mode in game_modes.keys():
            pool_key = f"pool:{mode}"
            queue_size = await r.zcard(pool_key)
            pool_status[mode] = {
                "queue_size": queue_size,
                "players_in_queue": queue_size
            }
        
        return {"pool_status": pool_status}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get pool status: {e}")

@router.get("/system_status")
async def get_system_status():
    try:
        # Get basic system info
        system_info = {
            "status": "online",
            "uptime": "running",
            "total_matches": 0,  # This could be tracked in Redis
            "active_queues": 0
        }
        
        # Count active queues
        with open("gameModes.json", 'r') as f:
            game_modes = json.load(f)
        
        active_queues = 0
        for mode in game_modes.keys():
            pool_key = f"pool:{mode}"
            if await r.zcard(pool_key) > 0:
                active_queues += 1
        
        system_info["active_queues"] = active_queues
        
        return {"system": system_info}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get system status: {e}")

@router.get("/recent_matches")
async def get_recent_matches():
    """Get recent match events for the dashboard"""
    try:
        # Get recent matches from Redis (stored by the worker)
        # For now, we'll return empty matches since the worker doesn't store them yet
        # In a real implementation, matches would be stored in Redis with timestamps
        return {"matches": []}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get recent matches: {e}")