from app.utils.redis_manager import r
import uuid, time, json, asyncio

# Config
try: 
    with open("gameModes.json", 'r') as f:
        game_rules = json.load(f)
        # print(game_rules)
except FileNotFoundError: 
    print("FATAL ERROR: gamemodes.json not found. Worker cannot start.")
    game_rules = {}

# Main Worker Loading
async def matchmaking_worker():
    print("******************************* Matchmaking worker started ********************************")
    
    while True:
        try: 
            # The main loop iterates through each configured game mode and tries to process its queue.
            for mode, rules in game_rules.items():
                # print(f"Mode: {mode}, Rules: {rules}")
                await process_queue_for_mode(mode, rules)
        except Exception as e:
            # This top-level error handling ensures the worker never crashes.
            print(f"CRITICAL ERROR in worker loop: {e}. Recovering...")
        
        await asyncio.sleep(2) # Run a full matchmaking cycle every 2 seconds.

async def process_queue_for_mode(mode: str, rules: dict):
    pool_key = f"pool:{mode}"
    match_size = rules['teamSize'] * rules['numTeams']

    # Not Enough Tickets 
    if await r.zcard(pool_key) < match_size:
        # print(f"## Not Enough Players: Need - {match_size - await r.zcard(pool_key)} - players more ")
        return
    
    # Grab the first N tickets from the top of the queue (lowest skill)
    # N -> match_size
    ticket_ids_bytes = await r.zrange(pool_key, 0, match_size - 1)
    
    if len(ticket_ids_bytes) == match_size:
        ticket_ids = [tid for tid in ticket_ids_bytes]
        
        # Atomically remove them
        if await r.zrem(pool_key, *ticket_ids):
            
            print(f"[ MATCH FOUND ] '{mode}': {ticket_ids}")
            
            # Publish events for the dashboard
            await r.publish("dashboard_events", json.dumps({"event": "log", "message": f"Match found for {mode}"}))
            await r.publish("dashboard_events", json.dumps({"event": "pool_updated", "gameMode": mode}))