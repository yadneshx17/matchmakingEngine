from app.utils.redis_manager import r
import json
from ..socket.socket_manager import sio

async def notification():
    pubsub = r.pubsub() 
    await pubsub.subscribe("match_found")

    async for msg in pubsub.listen():
        # print(f"notify raw Data: {msg}")

        if msg['type'] == "message":
            # print(f"Message:> {msg}")
            
            data = json.loads(msg["data"])
            # print(f"Notify Data:>  {data}")
          
            if data.get("event") == "match_found":
                player_ids = data.get("players", [])  
                match_id = data.get("match_id")

                print(f"Match found - {match_id} - for players: {player_ids}")

                for pid in player_ids:
                    # print(f"PID: {pid}")

                    sid = await r.hget("user_sids", pid)
                    # print(f"SID: {sid}")
                    if sid:
                        # sio.emit needs to be async
                        await sio.emit("send_notify", 
                                       {"message": f"Match {match_id} is ready!"}, 
                                       room=sid) 