from app.utils.redis_manager import r
import uuid, time, json, asyncio
from app.models.ticket import MatchmakingTicket, Player
from typing import List, Optional, Dict

# Config file impot 
try: 
    with open("gameModes.json", 'r') as f:
        game_rules = json.load(f)
except FileNotFoundError: 
    print("FATAL ERROR: gamemodes.json not found. Worker cannot start.")
    game_rules = {}

# Main Worker Loading
async def matchmaking_worker():
    print("(==>) MATCHMAKING WORKER: Starting engine...")
    print(f"[=] LOADED GAME MODES: {list(game_rules.keys())}")
    
    while True:
        try: 
            # The main loop iterates through each configured game mode and tries to process its queue.
            for mode, rules in game_rules.items():
                await process_queue_for_mode(mode, rules)
        except Exception as e:
            # This top-level error handling ensures the worker never crashes.
            print(f"[X] CRITICAL ERROR in worker loop: {e}. Recovering...")
        
        await asyncio.sleep(2) # Run a full matchmaking cycle every 2 seconds.

async def process_queue_for_mode(mode: str, rules: dict):
    pool_key = f"pool:{mode}"
    match_size = rules['teamSize'] * rules['numTeams']

    # Not Enough Tickets 
    if await r.zcard(pool_key) < match_size:
        return
    
    # Grab the first N tickets from the top of the queue (lowest skill)
    # N -> match_size
    # ticket_ids_bytes = await r.zrange(pool_key, 0, match_size - 1)
    
    anchor_ticket_tuple = await r.zpopmin(pool_key, 1)
    if not anchor_ticket_tuple:
        return

    anchor_ticket_id  = anchor_ticket_tuple[0][0]

    anchor_ticket = await get_ticket_by_id(anchor_ticket_id)
    if not anchor_ticket:
        return 

    # 3 - Dynamic Skill range: determine skill tolerance based on time.
    wait_time = time.time() - anchor_ticket.creationTime
    current_skill_tolerance = get_dynamic_skill_tolerance(wait_time, rules)
    anchor_average_skill = sum(p.skill for p in anchor_ticket.players) / len(anchor_ticket.players)
    min_skill = anchor_average_skill - current_skill_tolerance
    max_skill = anchor_average_skill + current_skill_tolerance

    # 4 - Team formation: find  a group tickets that can form a match
    match_proposal = await find_match_proposal(pool_key, anchor_ticket, match_size, min_skill, max_skill)

    if not match_proposal:
        anchor_average_skill = sum(p.skill for p in anchor_ticket.players) / len(anchor_ticket.players)
        await r.zadd(pool_key, {anchor_ticket.ticket : anchor_average_skill})
        return

    # 5. Team Balancing: Split the players into fair teams
    balanced_teams = balance_teams(match_proposal, rules)

    # 6. Latency Validation: Final check to ensure a low-lag game
    best_region = await is_match_viable_by_latency(match_proposal, rules)

    if best_region:
        # 7. Finalize the match: Atomically remove all players from the pool.
        matched_ticket_ids = [ticket.ticket for ticket in match_proposal]
        print(f"[*] MATCH FOUND: {mode} | Tickets: {matched_ticket_ids}")
        await r.zrem(pool_key, *matched_ticket_ids)

        # 8. Publish events for notifications and the dashboard
        await publish_match_found_events(mode, matched_ticket_ids, balanced_teams, best_region)
    else:
        # The latency check failed, This group can't play together
        # Put ALL tickets (including the anchor) back into the queue.
        print(f"[X] LATENCY CHECK FAILED: {mode} | Requeuing {len(match_proposal)} tickets")
        tickets_to_requeue = {}
        for ticket in match_proposal:
            ticket_average_skill = sum(p.skill for p in ticket.players) / len(ticket.players)
            tickets_to_requeue[ticket.ticket] = ticket_average_skill
        await r.zadd(pool_key, tickets_to_requeue)


async def find_match_proposal(pool_key: str, anchor_ticket: MatchmakingTicket, match_size: int, min_skill: int, max_skill: int):
    players_needed = match_size - len(anchor_ticket.players)

    candidates_ids = await r.zrangebyscore(pool_key, min_skill, max_skill)
    candidate_tickets = await get_tickets_by_ids([tid for tid in candidates_ids])

    candidate_tickets.sort(key=lambda t: len(t.players), reverse=True)

    proposal = [anchor_ticket]

    for ticket in candidate_tickets:
        if len(ticket.players) <= players_needed:
            proposal.append(ticket)
            players_needed -= len(ticket.players)
            if players_needed == 0:
                return proposal 

def balance_teams(proposal: List[MatchmakingTicket], rules: dict) -> Dict[str, List[Dict]]:
    if not proposal:
        return {}
    
    units = sorted(proposal, key=lambda t: sum(p.skill for p in t.players) / len(t.players), reverse=True)
    
    teams = [[] for _ in range(rules['numTeams'])]
    team_skills = [0.0] * rules['numTeams']

    for unit in units:
        if not unit.players:
            continue
            
        # Find the team with the lowest total skill
        weakest_team_index = team_skills.index(min(team_skills))
        
        # Add all players from this unit to the weakest team
        player_data = [p.model_dump() for p in unit.players]
        teams[weakest_team_index].extend(player_data)
        
        # Update team skill (sum of individual player skills)
        team_skills[weakest_team_index] += sum(p.skill for p in unit.players)

    return {f"team_{i+1}": team for i, team in enumerate(teams)}

async def is_match_viable_by_latency(proposal: List[MatchmakingTicket], rules: dict) -> Optional[str]:
    max_ping = rules.get('maxLatency', 150) # Default to 150ms if not specified
    
    viable_regions = set(r for r, p in proposal[0].latencyData.items() if p <= max_ping)

    for ticket in proposal[1:]:
        player_viable_regions = set(r for r, p in ticket.latencyData.items() if p <= max_ping)
        viable_regions.intersection_update(player_viable_regions)
        if not viable_regions:
            return None # Early exit if no common region is possible

    if not viable_regions:
        return None

    # Smart region selection: prioritize based on player preferences and latency
    return select_best_region(proposal, list(viable_regions))

def select_best_region(proposal: List[MatchmakingTicket], viable_regions: List[str]) -> str:
    """
    Selects the best region based on:
    - Player region preferences (highest priority)
    - Lowest average latency across all players
    """
    if not viable_regions:
        return None
    
    if len(viable_regions) == 1:
        return viable_regions[0]
    
    # Calculate scores for each region
    region_scores = {}
    
    for region in viable_regions:
        score = 0
        
        # 1. Preference score: count how many players prefer this region
        preference_count = 0
        for ticket in proposal:
            for player in ticket.players:
                for pref in player.regionPreference:
                    if region in pref and pref[region] > 0:
                        preference_count += pref[region]  # Weight by preference strength
        
        # 2. Latency score: lower average latency = higher score
        total_latency = 0
        player_count = 0
        for ticket in proposal:
            for player in ticket.players:
                if region in ticket.latencyData:
                    total_latency += ticket.latencyData[region]
                    player_count += 1
        
        avg_latency = total_latency / player_count if player_count > 0 else 999
        latency_score = max(0, 200 - avg_latency)  # Higher score for lower latency
        
        # 3. Combine scores (preference weight: 3x, latency weight: 1x)
        region_scores[region] = (preference_count * 3) + latency_score
    
    # Return region with highest score
    best_region = max(region_scores.items(), key=lambda x: x[1])[0]
    print(f">>> REGION SELECTION :: {len(proposal)} tickets")
    for region, score in sorted(region_scores.items(), key=lambda x: x[1], reverse=True):
        print(f"   {region}: {score}")
    print(f"   ✓ Selected: {best_region}")
    return best_region

def get_dynamic_skill_tolerance(wait_time: float, rules: dict) -> float:
    tolerance = float(rules['skillTolerance'])
    for steps in sorted(rules.get('expandSearchSteps', []), key=lambda x: x['afterSeconds']):
        if wait_time >= steps['afterSeconds']:
            tolerance = float(steps['newTolerance'])
    return tolerance

async def get_ticket_by_id(ticketId: str):
    try:
        ticket_json = await r.hget(f"ticket:{ticketId}", "ticketData")
        if not ticket_json:
            return None
        return MatchmakingTicket.model_validate_json(ticket_json)
    except Exception as e:
        print(f"[X] ERROR getting ticket {ticketId}: {e}")
        return None

async def get_tickets_by_ids(ticketIds: List[str]) -> List[MatchmakingTicket]:
    if not ticketIds: 
        return []

    # Get ticket data for each ticket ID
    tickets = []
    for tid in ticketIds:
        try:
            ticket_json = await r.hget(f"ticket:{tid}", "ticketData")
            if ticket_json:
                tickets.append(MatchmakingTicket.model_validate_json(ticket_json))
        except Exception as e:
            print(f"[X] ERROR getting ticket {tid}: {e}")
            continue
    return tickets

async def publish_match_found_events(mode: str, ticket_ids: List[str], teams: Dict, region: str):
    """Publishes events to the required Redis Pub/Sub channels."""
    match_id = str(uuid.uuid4())
    timestamp = time.time()
    
    # Clean, structured log message
    log_message = f"MATCH FOUND: {match_id} | Mode: {mode} | Region: {region} | Players: {len(ticket_ids)}"
    print(f"✓ MATCH: {log_message}")

    # Event for the NOTIFICATION service (to players)
    match_found_event = {
        "event": "match_found", 
        "matchId": match_id,
        "gameMode": mode, 
        "region": region,
        "teams": teams,
        "timestamp": timestamp,
        "ticketIds": ticket_ids
    }
    await r.publish("match_found", json.dumps(match_found_event))

    # Events for the DASHBOARD
    dashboard_log_event = {
        "event": "log", 
        "message": log_message,
        "timestamp": timestamp,
        "level": "info"
    }
    await r.publish("dashboard_events", json.dumps(dashboard_log_event))
    
    pool_updated_event = {
        "event": "pool_updated", 
        "gameMode": mode,
        "timestamp": timestamp,
        "action": "match_created"
    }
    await r.publish("dashboard_events", json.dumps(pool_updated_event))