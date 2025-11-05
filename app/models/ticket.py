from pydantic import BaseModel, Field
from typing import Dict, List
import time

class Player(BaseModel):
    playerName: str
    skill: int
    regionPreference: List[Dict[str, int]]

class MatchmakingTicket(BaseModel):
    ticket: str
    players: List[Player]
    gameMode: str
    regionPreference: List[Dict[str, int]]
    latencyData: Dict[str, int]
    creationTime: float = Field(default_factory=time.time)
    status: str = "searching"

class JoinQueueRequest(BaseModel):
    playerName: str
    skill: int
    regionPreference: Dict[str, int]