# client.py
import socketio
import asyncio
import os
from dotenv import load_dotenv
import requests

# Config
load_dotenv()
SERVER_URL = os.getenv("SERVER_URL", "http://localhost:5000")

# socket client instance
sio = socketio.AsyncClient()

parameters = {
    "player_name": "PlayerTwo",
    "player_skill": 120
}
response = requests.post('http://localhost:8000/api/v1/join_queue', params=parameters)

PLAYER_ID = response.json().get('player_id')

@sio.event
async def connect():
    print(f"Connected to server as player '{PLAYER_ID}'")

@sio.event
async def disconnect():
    print("Disconnnected from server")

# Custom Event handler for when a match is found for this clientt
@sio.on("send_notify")
async def on_match_found(data):
    print("------------------------------------")
    print(f">>> Match Found! Details: {data}")

async def main():
    print(f"Attempting to connect to {SERVER_URL}...")
    try:
        await sio.connect(SERVER_URL, auth={"playerId": PLAYER_ID})
        # The wait() call will keep the client alive to listen for events.
        # It will only exit if the connection is dropped.
        await sio.wait()
    except socketio.exceptions.ConnectionError as e:
        print(f"Connection failed: The server might be down. Details: {e}")
    except Exception as e:
        print(f"an unexpected error occurred: {e}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Client shutting down.")