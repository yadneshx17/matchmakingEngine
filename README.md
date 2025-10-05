# Real-Time Matchmaking Engine (MVP)

This is a **MVP** of a real-time matchmaking engine built with **FastAPI + Redis + Socket.IO**.  
It handles **player queueing, matchmaking, notifications, and pub/sub events**. The whole flow works end-to-end, and clients get notified when a match is found.  


## Architecture
<img width="963" height="603" alt="image" src="https://github.com/user-attachments/assets/5107e059-50f3-42b0-aed4-559cf541b62a" />

## 🧰 Run Locally

Clone the repo:

```bash
$ git clone https://github.com/yadneshx17/matchmakingEngine.git
$ cd matchmakingEngine
```

Install dependencies:

```bash
$ pip install -r requirements.txt
```

Run the server:

```bash
$ uvicorn app.main:socket_app --port 8000 --reload
```
**  Make sure Redis is running**

Using Docker (recommended):
```bash
$ docker run -d --name redis -p 6379:6379 redis
```
*Redis must be running before starting the app — the backend depends on it.*


## 🧪 Test It

Open another terminal and run the Socket.IO client:

```py
$ python client.py    
```


## 🧰 Run Locally

Clone the repo:

```bash
$ git clone https://github.com/yadneshx17/matchmakingEngine.git
$ cd matchmakingEngine
```

Install dependencies:

```bash
$ pip install -r requirements.txt
```

Run the server:

```bash
$ uvicorn app.main:socket_app --port 8000 --reload
```
**  Make sure Redis is running**

Using Docker (recommended):
```bash
$ docker run -d --name redis -p 6379:6379 redis
```
*Redis must be running before starting the app — the backend depends on it.*


## 🧪 Test It

Open another terminal and run the Socket.IO client:

```py
$ python client.py    
```

**Flow:**
1. Player joins queue → stored in Redis  
2. Matchmaking worker Loops through Queue  
3. Worker forms matches and publishes `"match_found"` events  
4. Notification service emits WebSocket events to connected clients  
5. Clients instantly see that a match is found

## ✅ What's Done
- Player service
- Core matchmaking worker  
- Redis pub/sub for events  
- WebSocket + Socket.IO notifications  
- Background workers for scaling  
- MVP client to test matches  

## 🚧 What's Next ( Planning )
- Hook up a proper **Player Service** with metadata & auth  
- Smarter matchmaking logic (skill buckets, regions, fairness)  
- Add persistence & monitoring for production use  
- Stress testing for real-world scenarios  

## 🧑‍💻 Tech Stack
- FastAPI (for API + app lifecycle)  
- Redis (queue, pub/sub, metadata)  
- Socket.IO (real-time client/server notifications)  
- Python asyncio (background workers)  

## 🎯 Why This Exists
I built this to explore how a **scalable real-time matchmaking system** can work in practice.  
Right now it’s just a simple MVP, but it gives a solid foundation to expand and build upon for adding complexity later.


## 📝 Note
Yeah, I wrote all the comments myself - **not AI slop**
---
