from fastapi import FastAPI
import socketio
import asyncio
from app.socket.socket_manager import sio
from app.routers import player
from .worker.matchmaker import matchmaking_worker
from .notification.notifications import notification
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware


# run background worker on startup
async def lifespan(app: FastAPI):
    task = asyncio.create_task(matchmaking_worker())
    notify_task = asyncio.create_task(notification())
    print("Matchmaking worker startedddddd")

    yield  # <-- App runs while this is paused

    # Shutdown
    task.cancel()
    notify_task.cancel()
    print("Matchmaking worker stopped")

# FastAPI App
app = FastAPI(lifespan=lifespan)

# Bind WS
socket_app = socketio.ASGIApp(sio, other_asgi_app=app)

# Include Routers
app.include_router(player.router, prefix="/api/v1", tags=["players"])

# CORS
app.add_middleware (
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True, 
    allow_methods=["*"],  
    allow_headers=["*"],
)

# Root
@app.get("/")
async def root():
    return {"message": "Real-time Scalable Matchmaking Engine"}