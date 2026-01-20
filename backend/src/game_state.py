"""
game_state.py

This file manages the "Brain" of the game.
Now supports MULTIPLE rooms with unique room codes!
"""

import uuid
import time
import random
import string
from typing import Dict, Any, List, Optional
from flask_socketio import emit
from .constants import PROBLEM_TEMPLATES

# --------------------------
# GLOBAL STATE
# --------------------------

# Maps socket ID to (player_id, room_code)
socket_to_player: Dict[str, tuple[str, str]] = {}

# Dictionary of all active rooms
# Structure: { 'ABCD12': { 'players': {}, 'gameStatus': 'lobby', 'winner': None }, ... }
rooms: Dict[str, Dict[str, Any]] = {}

# --------------------------
# HELPER FUNCTIONS
# --------------------------

def generate_room_code() -> str:
    """
    Generate a unique 6-character room code.
    Uses uppercase letters and numbers.
    """
    while True:
        # Generate random 6-char code
        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        # Ensure it's unique
        if code not in rooms:
            return code

def get_or_create_room(room_code: Optional[str] = None) -> tuple[str, Dict[str, Any]]:
    """
    Get an existing room or create a new one.
    Returns (room_code, room_dict)
    """
    if room_code and room_code in rooms:
        return room_code, rooms[room_code]
    
    # Create new room
    if not room_code:
        room_code = generate_room_code()
    
    rooms[room_code] = {
        'players': {},
        'gameStatus': 'lobby',
        'winner': None,
        'roomCode': room_code
    }
    
    print(f'Created new room: {room_code}')
    return room_code, rooms[room_code]

def get_room(room_code: str) -> Optional[Dict[str, Any]]:
    """Get a room by code, returns None if doesn't exist."""
    return rooms.get(room_code)

def delete_room_if_empty(room_code: str):
    """Delete a room if it has no players."""
    if room_code in rooms and len(rooms[room_code]['players']) == 0:
        del rooms[room_code]
        print(f'Deleted empty room: {room_code}')

def generate_card() -> Dict[str, Any]:
    """
    Creates a new random problem card for a player.
    """
    template = random.choice(PROBLEM_TEMPLATES).copy()
    card = {
        'id': str(uuid.uuid4()),
        'problem': template['problem'].copy(),
        'reward': template.get('reward'),
        'challenge': template.get('challenge')
    }
    return card

def check_win_condition(room_code: str) -> bool:
    """
    Check if the game in this room should end.
    Returns True if game ended.
    """
    room = get_room(room_code)
    if not room:
        return False
    
    active_players = [pid for pid, p in room['players'].items() 
                     if not p.get('isEliminated', False)]
    
    if len(active_players) == 1:
        room['gameStatus'] = 'ended'
        room['winner'] = active_players[0]
        
        emit('game_ended', {
            'winner': room['winner'],
            'winnerName': room['players'][active_players[0]]['username']
        }, room=room_code)
        return True
        
    elif len(active_players) == 0 and room['players']:
        room['gameStatus'] = 'ended'
        emit('game_ended', {'winner': None}, room=room_code)
        return True
        
    return False

def apply_reward(room_code: str, player_id: str, reward: Dict[str, Any], is_debug: bool = False):
    """
    Apply a reward in a specific room.
    """
    room = get_room(room_code)
    if not room:
        return
    
    effect_type = reward['effect']
    value = reward['value']
    
    # 1. ADD TIME
    if effect_type == 'add_time':
        if player_id in room['players']:
            room['players'][player_id]['timerEndTime'] += value * 1000
            emit('reward_applied', {
                'playerId': player_id,
                'effect': 'add_time',
                'value': value
            }, room=room_code)
    
    # 2. REMOVE TIME (Random)
    elif effect_type == 'remove_time':
        candidates = [pid for pid in room['players'].keys() if not room['players'][pid]['isEliminated']]
        other_players = [pid for pid in candidates if pid != player_id]
        
        if is_debug and not other_players and player_id in candidates:
            other_players = [player_id]
            
        if other_players:
            target_id = random.choice(other_players)
            room['players'][target_id]['timerEndTime'] = max(
                time.time() * 1000,
                room['players'][target_id]['timerEndTime'] - (value * 1000)
            )
            emit('reward_applied', {
                'playerId': target_id,
                'effect': 'remove_time',
                'value': value,
                'fromPlayer': player_id
            }, room=room_code)
    
    # 3. TARGETED DEBUFF
    elif effect_type in ['remove_time_targeted', 'flashbang_targeted']:
        candidates = [pid for pid in room['players'].keys() if not room['players'][pid]['isEliminated']]
        other_players = [pid for pid in candidates if pid != player_id]
        
        if is_debug and not other_players:
            other_players = [player_id]
            
        if other_players:
            room['players'][player_id]['pendingTargetedReward'] = reward
            
            emit('target_selection_required', {
                'effect': effect_type,
                'value': value,
                'availableTargets': [{
                    'playerId': pid,
                    'username': room['players'][pid]['username'],
                    'timeRemaining': max(0, int((room['players'][pid]['timerEndTime'] - time.time() * 1000) / 1000))
                } for pid in other_players]
            }, room=room['players'][player_id]['socket_id'])
            
    # 4. GLOBAL ATTACK
    elif effect_type == 'remove_time_all':
        candidates = [pid for pid in room['players'].keys() if not room['players'][pid]['isEliminated']]
        other_players = [pid for pid in candidates if pid != player_id]
        
        if is_debug and not other_players:
            other_players = [player_id]
            
        affected_players = []
        for target_id in other_players:
            room['players'][target_id]['timerEndTime'] = max(
                time.time() * 1000,
                room['players'][target_id]['timerEndTime'] - (value * 1000)
            )
            affected_players.append({
                'playerId': target_id,
                'username': room['players'][target_id]['username']
            })
        
        if affected_players:
            emit('reward_applied', {
                'effect': 'remove_time_all',
                'value': value,
                'fromPlayer': player_id,
                'affectedPlayers': affected_players
            }, room=room_code)
