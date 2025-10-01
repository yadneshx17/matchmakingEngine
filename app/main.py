from fastapi import FastAPI
import socketio
from app.socket.socket_manager import sio
from app.routers import player


app = FastAPI()
socket_app = socketio.ASGIApp(sio, other_asgi_app=app)

app.include_router(player.router, prefix="/api/v1", tags=["players"])

@app.get("/")
async def root():
    return {"message": "Real-time Scalable Matchmaking Engine"}