import socketio 
from ..utils.redis_manager import r

# currently allowing all origins for dev purpose.
# later replace with trusted domains
ALLOWED_ORIGINS = ["*"]

# socket instance 
sio = socketio.AsyncServer(async_mode="asgi", cors_allowed_origins=ALLOWED_ORIGINS)

# Import events to register them with the sio instance

@sio.event
async def connect(sid, environ, auth):
    if auth and 'playerId' in auth:
        player_id = auth['playerId']
        print(f'Player {player_id} connected with SID {sid}')
        await r.hset("user_sids", player_id, sid) # Store mapping ( playerId -> sid )
    else:
        print(f'Anonymous client connected: {sid}. Disconnecting.')
        await sio.disconnect(sid)

@sio.event
async def disconnect(sid):
    # We need to find which playerId this sid belonged to and remove it
    # This is a bit more complex we might need a reverse mapping too ( sid -> playerId)
    # For now lets focus on the connect part.
    print('disconnect ', sid)