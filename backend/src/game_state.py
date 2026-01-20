"""
game_state.py

This file manages the "Brain" of the game.
It stores the current state (who is playing, what are the scores)
and contains logic to modify that state (applying rewards, checking winners).
"""

import uuid
import time
import random
from typing import Dict, Any, List
from flask_socketio import emit
from .constants import PROBLEM_TEMPLATES

# --------------------------
# GLOBAL STATE
# --------------------------
# Since we are using a simple in-memory storage, we keep everything in global variables.
# In a real production app, you might use a database like Redis or PostgreSQL.

# Maps a socket connection ID (from the browser) to a Player ID.
socket_to_player: Dict[str, str] = {}

# The main game state object.
game_state = {
    'players': {},           # Dictionary of connected players
    'gameStatus': 'lobby',   # Game phase: 'lobby' | 'playing' | 'ended'
    'roomCode': 'ROOM1',     # Room identifier (we only support one room for now)
    'winner': None           # ID of the winner
}

# --------------------------
# HELPER FUNCTIONS
# --------------------------

def generate_card() -> Dict[str, Any]:
    """
    Creates a new random problem card for a player.
    It takes a template from PROBLEM_TEMPLATES and gives it a unique ID.
    """
    template = random.choice(PROBLEM_TEMPLATES).copy()
    card = {
        'id': str(uuid.uuid4()),               # Unique ID for this specific card
        'problem': template['problem'].copy(), # The coding problem
        'reward': template.get('reward'),      # What you get if you solve it
        'challenge': template.get('challenge') # Optional extra constraints
    }
    return card

def check_win_condition() -> bool:
    """
    Checks if the game should end. 
    The game ends when only 1 player remains (Battle Royale style).
    Returns True if game ended.
    """
    # Filter for players who are NOT eliminated
    active_players = [pid for pid, p in game_state['players'].items() 
                     if not p.get('isEliminated', False)]
    
    # If 1 survivor remains
    if len(active_players) == 1:
        game_state['gameStatus'] = 'ended'
        game_state['winner'] = active_players[0]
        
        # Broadcast the winner to everyone
        emit('game_ended', {
            'winner': game_state['winner'],
            'winnerName': game_state['players'][active_players[0]]['username']
        }, broadcast=True)
        return True
        
    # If 0 survivors (shouldn't happen, but good to handle)
    elif len(active_players) == 0 and game_state['players']:
        game_state['gameStatus'] = 'ended'
        emit('game_ended', {'winner': None}, broadcast=True)
        return True
        
    return False

def apply_reward(player_id: str, reward: Dict[str, Any], is_debug: bool = False):
    """
    Apply a special effect (Buff/Debuff) when a card is solved.
    
    Args:
        player_id: The ID of the player who solved the card.
        reward: The reward dictionary defined in the card.
        is_debug: Used for testing to allow targeting yourself.
    """
    effect_type = reward['effect']
    value = reward['value']
    
    # 1. ADD TIME (Heal)
    if effect_type == 'add_time':
        if player_id in game_state['players']:
            # Add time to the player's deadline
            game_state['players'][player_id]['timerEndTime'] += value * 1000
            
            # Tell everyone this happened so their UI updates
            emit('reward_applied', {
                'playerId': player_id,
                'effect': 'add_time',
                'value': value
            }, broadcast=True)
    
    # 2. REMOVE TIME (Attack Random)
    elif effect_type == 'remove_time':
        # Find valid targets
        candidates = [pid for pid in game_state['players'].keys() if not game_state['players'][pid]['isEliminated']]
        other_players = [pid for pid in candidates if pid != player_id]
        
        # Debug override
        if is_debug and not other_players and player_id in candidates:
            other_players = [player_id]
            
        if other_players:
            target_id = random.choice(other_players)
            # Reduce their time (make their deadline sooner) by moving it closer to now
            game_state['players'][target_id]['timerEndTime'] = max(
                time.time() * 1000,
                game_state['players'][target_id]['timerEndTime'] - (value * 1000)
            )
            emit('reward_applied', {
                'playerId': target_id,
                'effect': 'remove_time',
                'value': value,
                'fromPlayer': player_id
            }, broadcast=True)
    
    # 3. TARGETED DEBUFF (Attack Specific Player)
    elif effect_type in ['remove_time_targeted', 'flashbang_targeted']:
        # We don't apply it immediately. We ask the client to pick a target.
        candidates = [pid for pid in game_state['players'].keys() if not game_state['players'][pid]['isEliminated']]
        other_players = [pid for pid in candidates if pid != player_id]
        
        if is_debug and not other_players:
            other_players = [player_id]
            
        if other_players:
            # Store the reward details so we can apply them after selection
            game_state['players'][player_id]['pendingTargetedReward'] = reward
            
            # Send list of targets to the player
            emit('target_selection_required', {
                'effect': effect_type,
                'value': value,
                'availableTargets': [{
                    'playerId': pid,
                    'username': game_state['players'][pid]['username'],
                    'timeRemaining': max(0, int((game_state['players'][pid]['timerEndTime'] - time.time() * 1000) / 1000))
                } for pid in other_players]
            }, room=game_state['players'][player_id]['socket_id']) # Only send to THIS player
            
    # 4. GLOBAL ATTACK (Nuke)
    elif effect_type == 'remove_time_all':
        candidates = [pid for pid in game_state['players'].keys() if not game_state['players'][pid]['isEliminated']]
        other_players = [pid for pid in candidates if pid != player_id]
        
        if is_debug and not other_players:
            other_players = [player_id]
            
        affected_players = []
        for target_id in other_players:
            game_state['players'][target_id]['timerEndTime'] = max(
                time.time() * 1000,
                game_state['players'][target_id]['timerEndTime'] - (value * 1000)
            )
            affected_players.append({
                'playerId': target_id,
                'username': game_state['players'][target_id]['username']
            })
        
        if affected_players:
            emit('reward_applied', {
                'effect': 'remove_time_all',
                'value': value,
                'fromPlayer': player_id,
                'affectedPlayers': affected_players
            }, broadcast=True)
