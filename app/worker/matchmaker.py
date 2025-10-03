from app.utils.redis_manager import r
import uuid, time, json, asyncio

async def matchmaking_worker():
    # Worker Loop
    print("<<< Matchmaking worker started >>>")

    while True:
        pubsub = r.pubsub()
        await pubsub.subscribe("matchmaking-events")
        try:
    
            # 1. Check if there are enough players in the queue
            queue_size = await r.zcard("queue") # zcard gets the size of the sorted set
            if queue_size < 2:
                await asyncio.sleep(5) # Wait before checking again
                continue

            # 2. Get one player to build a match around.
            # ZPOPMIN  -> atomically gets and removes the lowest-ranked player.
            player1_id, player1_skill = (await r.zpopmin("queue", 1))[0]
            print(f"Attempting to build match for Player {player1_id} (Skill: {player1_skill})")
            
            # 3. Define the search range for a good match.
            skill_tolerance = 50 # This should come from a ruleset/config
            min_skill = player1_skill - skill_tolerance
            max_skill = player1_skill + skill_tolerance

            # 4. Search for a suitable opponent in that skill range.
            # ZRANGEBYSCORE... WITHSCORES LIMIT 0 1
            potential_opponents = await r.zrangebyscore("queue", min_skill, max_skill, start=0, num=1, withscores=True)

            if potential_opponents:
                # 5. We found a match!
                opponent_tuple = potential_opponents[0]
                player2_id, player2_skill = opponent_tuple[0], opponent_tuple[1]
                
                # Remove the matched player from the queue
                await r.zrem("queue", player2_id)
                
                # A. Create the match details
                match_id = str(uuid.uuid4())
                players_in_match = [
                    {"player_id": player1_id, "skill": player1_skill},
                    {"player_id": player2_id, "skill": player2_skill}
                ]
                
                # B. Create the event payload to publish
                event_payload = {
                    "event": "match_found",
                    "match_id": match_id,
                    "players": [p["player_id"] for p in players_in_match] # Send a simple list of IDs
                }

                # C. Publish the event to the 'match_found' channel
                await r.publish("match_found", json.dumps(event_payload))
                
                print(f"*** SUCCESS: Matched {player1_id} with {player2_id}. Published event for match {match_id}.")

            else:
                # 6. No suitable match found. Put player 1 back in the queue.
                print(f"INFO: No match for {player1_id}. Returning to queue.")
                await r.zadd("queue", {player1_id: player1_skill})
        except Exception as e:
            print(f"An error occurred in the matchmaking loop: {e}")

        # Wait for a few seconds before the next matchmaking cycle
        await asyncio.sleep(5)