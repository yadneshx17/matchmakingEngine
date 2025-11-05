from app.utils.redis_manager import r
import json
from ..socket.socket_manager import sio


async def dashboardNotify():
    pubsub = r.pubsub() 
    await pubsub.subscribe("dashboard_events", "match_found")

    print("DASHBOARD: Starting notification listener...")

    async for msg in pubsub.listen():
        if msg['type'] == "message":
            try:
                data = json.loads(msg['data'])
                event_type = data.get("event")
                
                if event_type == "log":
                    print(f"DASHBOARD LOG: {data.get('message')}")
                    # Send log events to dashboard clients
                    await sio.emit("dashboard_log", {
                        "message": data.get('message'),
                        "timestamp": data.get('timestamp'),
                        "level": data.get('level', 'info')
                    })
                elif event_type == "pool_updated":
                    game_mode = data.get('gameMode')
                    action = data.get('action', 'unknown')
                    print(f"POOL UPDATE: {game_mode} | Action: {action}")
                    # Send pool updates to dashboard clients
                    await sio.emit("pool_updated", {
                        "gameMode": game_mode,
                        "action": action,
                        "timestamp": data.get('timestamp')
                    })
                elif event_type == "match_found":
                    print(f"MATCH FOUND: {data.get('matchId')} | Mode: {data.get('gameMode')}")
                    # Send match found events to dashboard clients
                    await sio.emit("match_found", {
                        "matchId": data.get('matchId'),
                        "gameMode": data.get('gameMode'),
                        "region": data.get('region'),
                        "teams": data.get('teams'),
                        "timestamp": data.get('timestamp'),
                        "ticketIds": data.get('ticketIds')
                    })
                else:
                    print(f"DASHBOARD EVENT: {event_type} | Data: {data}")
                    
            except json.JSONDecodeError as e:
                print(f"DASHBOARD: Invalid JSON received: {e}")
            except Exception as e:
                print(f"DASHBOARD: Error processing event: {e}")