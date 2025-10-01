import socketio 

ALLOWED_ORIGINS = []

sio = socketio.AsyncServer(asyc_mode="asgi", cors_alloweed_origins=ALLOWED_ORIGINS)

# Import events to register them with the sio instance
