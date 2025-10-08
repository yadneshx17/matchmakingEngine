from app.utils.redis_manager import r
import json
from ..socket.socket_manager import sio


async def dashboardNotify():
    pubsub = r.pubsub() 
    await pubsub.subscribe("dashboard_events")

    async for msg in pubsub.listen():
        # print(msg['type'])
        if msg['type'] == "message":
            data = json.loads(msg['data'])
            # if data.get("event") == "pool_updated":
                # print(f"Data: {data.get('gameMode')}")