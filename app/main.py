from fastapi import FastAPI
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
import socketio
import asyncio
from app.socket.socket_manager import sio
from .routers import player
from .worker.matchmaker import matchmaking_worker
from .notification.notifications import notification
from .notification.dashboardnotify import dashboardNotify

# run background worker on startup
async def lifespan(app: FastAPI):
    task = asyncio.create_task(matchmaking_worker())
    notify_task = asyncio.create_task(notification())
    dashboard = asyncio.create_task(dashboardNotify())
    print("----------------------------------- MatchEngine started -----------------------------------")

    yield  # <-- App runs while this is paused

    # Shutdown
    task.cancel()
    notify_task.cancel()
    dashboard.cancel()
    print("----------------------------------- MatchEngine stopped -----------------------------------")

# FastAPI App
app = FastAPI(lifespan=lifespan)

# Bind WS
socket_app = socketio.ASGIApp(sio, other_asgi_app=app)

# Include Routers
app.include_router(player.router, prefix="/api/v2", tags=["players"])

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