# Real-Time Matchmaking Engine (MVP)

This is a real-time, rule-driven matchmaking engine built with **FastAPI + Redis + Socket.IO**.
It features a **stateless**, **event-driven architecture** with **dynamic skill-based search**, **region validation**, and a **flexible ticketing system** — all visualized live through a real-time **dashboard**.

## 🌐 Live Dashboard

**🎮 Try it live:** [https://matchmaking-engine.vercel.app/](https://matchmaking-engine.vercel.app/)

The live dashboard provides:
- **Real-time Player Pool Monitoring** - Track active connections and player statistics
- **Server Events Log** - Monitor engine status, configuration loading, and system events
- **Match Events Log** – Watch the engine form matches and publish events in real time
- **Interactive Simulation** - Test different game modes and player scenarios
- **Live Statistics** - View total players, average skill levels, and regional distribution
- **Matchmaking Controls** - Clear pool, trigger backend matching, and monitor queue status  

**NOTE : *The dashboard is hosted, but the engine (worker + Redis) should be run locally to see live matchmaking behavior.***

---

## Architecture Overview
<img width="963" height="603" alt="image" src="https://github.com/user-attachments/assets/5107e059-50f3-42b0-aed4-559cf541b62a" />


#### Core Components:

- **FastAPI Server**: Handles player requests and creates matchmaking tickets.

- **Redis:** Manages player pools, stores metadata, and handles pub/sub communication.

- **Socket.IO:** Powers real-time event streaming between backend and dashboard.

- **Worker Process:** Continuously matches players based on configurable JSON rules.

---

## How to Run Locally

**1. Clone the Repository:**

```bash
$ git clone https://github.com/yadneshx17/matchmakingEngine.git
$ cd matchmakingEngine
```

**2. Install dependencies:**

```bash
$ pip install -r requirements.txt
```
**3. Start Redis (Required)**

Using Docker (recommended):
```bash
$ docker run -d --name redis -p 6379:6379 redis
```
Or start it manually if Redis is installed locally.

**NOTE:** *Redis must be running before starting the app — the backend depends on it.*

**4. Run the server:**

```bash
$ uvicorn app.main:socket_app --port 8000 --reload
```
**5. Test it**

> All testing and simulation can be performed directly via the hosted live dashboard

**From the dashboard you can:**

- Add players to the queue
- Trigger matchmaking for different game modes
- Monitor real-time events, player pools, and system logs

---

## Matchmaking Flow

**1.** A player joins the queue (API request).

**2.** A Ticket is created and stored in the Redis pool (skill-sorted).

**3.** The worker applies rule-based matching (from JSON config) to find fair matches.

**4.** Validated matches are published as events via Redis Pub/Sub.

**5.** The dashboard and connected clients receive instant match notifications..

---

## Features Complete

- **High-Performance Player Pool** – Utilizes Redis Sorted Sets for fast, skill-based and region-aware player lookups.
- **Rule-Driven Matchmaking Engine** – Fully configurable via external JSON rulesets without modifying core code.
- **Stateless, Scalable Workers** – Horizontally scalable matchmaking workers for concurrent, distributed processing.
- **Dynamic Search Expansion** – Gradually increases skill tolerance and region flexibility based on queue time.
- **Latency-Aware Region Validation** – Ensures optimal server selection by validating common low-latency regions.
- **Event-Driven Communication** – Implements decoupled service interaction using Redis Pub/Sub channels.
- **Real-Time Dashboard Interface** – WebSocket-powered dashboard for monitoring player pools and match events.
- **Interactive Player Simulation** – In-browser simulation to test different game modes and matchmaking scenarios.
- **Comprehensive Server Logging** – Structured event logs for debugging, analytics, and audit tracking.

---

## Game Modes Configuration

The Matchmaking engine supports **configurable game modes** defined in `gameModes.json`, allowing the system to adapt to different matchmaking rules dynamically.

#### Configuration Fields:
- **Team Structure** - Team size and number of teams
- **Skill Matching** - Initial skill tolerance and auto-expansion settings
- **Queue Requirements** - Minimum tickets/players required to form a match
- **Time-based Expansion** - Progressive widening of tolerance over time

**Available Game Modes:**
- `1v1_duel` - Classic 1v1 with 75 skill tolerance
- `2v2_clash` - Team-based 2v2 with 100 skill tolerance  
- `3v3_arena` - Team-based 3v3 battles
- `5v5_arena` - Large team 5v5 matches

**Dynamic Skill Expansion:**
The system automatically expands skill tolerance over time to ensure matches are found:
- After 20-30 seconds: Moderate tolerance increase
- After 40-60 seconds: Significant tolerance expansion

---

## 🧑‍💻 Tech Stack
- FastAPI (for API + app lifecycle)  
- Redis (queue, pub/sub, metadata)  
- Socket.IO (real-time client/server notifications)  
- Python asyncio (background workers)  

---

# System Architecture

```
matchmaking_engine/
└─ app/
   ├─ main.py                  # FastAPI server entry point
   ├─ models/                  # Pydantic models (e.g., Ticket, Player)
   ├─ notifications/           # Notification services
   ├─ routers/                 # API route definitions
   │  └─ player.py             # Player service & dashboard endpoints
   ├─ sockets/                 # Socket.IO management
   ├─ utils/                   # Utility/helper modules
   │  └─ redis_manager.py      # Redis connection & helpers
   └─ workers/                 # Background matchmaking logic
      └─ matchmaker.py
```

---

## 🎯 Why This Exists
This project was built to explore the internals of scalable, **real-time matchmaking systems**, the of kind used in multiplayer games or skill-based pairing apps.
It demonstrates clean architecture, decoupled components, and real-time visualization for debugging and experimentation.
> It’s an MVP — but it lays a strong foundation for production-grade systems with scaling and analytics