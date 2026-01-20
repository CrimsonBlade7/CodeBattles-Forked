"""
events.py

This file handles all the network events.
Updated to support multiple rooms with unique room codes!
"""

import time
import uuid
from flask import request
from flask_socketio import emit, join_room, leave_room

# Import from our other modules
from .extensions import socketio
from .game_state import (
    socket_to_player, rooms,
    get_or_create_room, get_room, delete_room_if_empty,
    generate_card, apply_reward, check_win_condition
)
from .utils import execute_code

# --------------------------
# CONNECTION EVENTS
# --------------------------

@socketio.on('connect')
def handle_connect():
    """Called when a client opens a connection."""
    print(f'Client connected: {request.sid}')
    emit('connected', {'socket Id': request.sid})

@socketio.on('disconnect')
def handle_disconnect():
    """Called when a client drops connection."""
    socket_id = request.sid
    print(f'Client disconnected: {socket_id}')
    
    # Clean up player data
    if socket_id in socket_to_player:
        player_id, room_code = socket_to_player[socket_id]
        room = get_room(room_code)
        
        if room and player_id in room['players']:
            player_name = room['players'][player_id]['username']
            del room['players'][player_id]
            
            # Tell others in the room they left
            emit('player_left', {
                'playerId': player_id,
                'username': player_name
            }, room=room_code)
            
            # Check win condition
            check_win_condition(room_code)
            
            # Clean up empty room
            delete_room_if_empty(room_code)
        
        del socket_to_player[socket_id]

# --------------------------
# GAME LOBBY EVENTS
# --------------------------

@socketio.on('join_room')
def handle_join_room(data):
    """
    Player wants to join a room.
    Creates player object and adds to room state.
    """
    username = data.get('username', '').strip()
    room_code = data.get('roomCode', '').strip().upper()
    
    if not username:
        emit('join_error', {'message': 'Username required'})
        return
    
    socket_id = request.sid
    player_id = str(uuid.uuid4())
    
    # Get or create room
    if room_code:
        # Joining existing room
        room = get_room(room_code)
        if not room:
            emit('join_error', {'message': f'Room {room_code} not found'})
            return
    else:
        # Create new room
        room_code, room = get_or_create_room()
    
    # Join the Flask-SocketIO room for proper broadcasting
    join_room(room_code)
    
    # Track socket -> (player, room) mapping
    socket_to_player[socket_id] = (player_id, room_code)
    
    # Create player
    player = {
        'id': player_id,
        'username': username,
        'socket_id': socket_id,
        'timerEndTime': None,
        'isEliminated': False,
        'eliminatedAt': None,
        'currentProblem': None,
        'cards': [],
        'isTimeFrozen': False,
        'frozenUntil': None
    }
    
    room['players'][player_id] = player
    
    # Broadcast to room
    emit('player_joined', {
        'playerId': player_id,
        'username': username,
        'roomCode': room_code
    }, room=room_code)
    
    # Send game state to new player
    emit('game_state', {
        'players': room['players'],
        'gameStatus': room['gameStatus'],
        'roomCode': room_code,
        'winner': room.get('winner')
    }, room=socket_id)
    
    print(f'Player {username} ({player_id}) joined room {room_code}')


@socketio.on('start_game')
def handle_start_game():
    """Host starts the game."""
    socket_id = request.sid
    
    if socket_id not in socket_to_player:
        emit('error', {'message': 'Not connected'})
        return
    
    player_id, room_code = socket_to_player[socket_id]
    room = get_room(room_code)
    
    if not room or not room['players']:
        emit('error', {'message': 'No players in game'})
        return
    
    # First player is host
    first_player_id = list(room['players'].keys())[0]
    if player_id != first_player_id:
        emit('error', {'message': 'Only host can start game'})
        return
    
    room['gameStatus'] = 'playing'
    
    # Set timer: 5 minutes from now
    timer_end_time = (time.time() + 300) * 1000
    for pid in room['players'].keys():
        room['players'][pid]['timerEndTime'] = timer_end_time
    
    # Deal 5 cards to each player
    for pid in room['players'].keys():
        cards = [generate_card() for _ in range(5)]
        room['players'][pid]['cards'] = cards
    
    # Broadcast to room
    emit('game_started', {
        'players': {pid: {
            'id': p['id'],
            'username': p['username'],
            'timerEndTime': p['timerEndTime'],
            'isEliminated': p['isEliminated'],
            'eliminatedAt': p.get('eliminatedAt'),
            'currentProblem': p['currentProblem'],
            'cards': p['cards']
        } for pid, p in room['players'].items()}
    }, room=room_code)
    
    print(f'Game started in room {room_code}')

# --------------------------
# GAMEPLAY EVENTS
# --------------------------

@socketio.on('select_card')
def handle_select_card(data):
    """Player selected a card."""
    socket_id = request.sid
    if socket_id not in socket_to_player: return
    
    player_id, room_code = socket_to_player[socket_id]
    room = get_room(room_code)
    if not room: return
    
    card_id = data.get('cardId')
    if player_id not in room['players']: return
    
    player = room['players'][player_id]
    card = next((c for c in player['cards'] if c['id'] == card_id), None)
    if not card:
        emit('error', {'message': 'Card not found'})
        return
    
    player['currentProblem'] = card_id
    
    emit('card_selected', {
        'playerId': player_id,
        'cardId': card_id,
        'problem': card['problem']
    }, room=room_code)


@socketio.on('submit_solution')
def handle_submit_solution(data):
    """Player submitted code."""
    socket_id = request.sid
    if socket_id not in socket_to_player: return
    
    player_id, room_code = socket_to_player[socket_id]
    room = get_room(room_code)
    if not room: return
    
    card_id = data.get('cardId')
    code = data.get('code', '')
    
    if player_id not in room['players']: return
    player = room['players'][player_id]
    
    if player['isEliminated']:
        emit('error', {'message': 'Player is eliminated'})
        return
    
    card = next((c for c in player['cards'] if c['id'] == card_id), None)
    if not card:
        emit('error', {'message': 'Card not found'})
        return
    
    if player['currentProblem'] != card_id:
        emit('error', {'message': 'Card is not currently selected'})
        return
    
    # Execute code
    result = execute_code(code, card['problem']['functionSignature'], card['problem']['testCases'])
    
    if result['passed']:
        # Remove card, clear selection
        player['cards'] = [c for c in player['cards'] if c['id'] != card_id]
        player['currentProblem'] = None
        
        # Apply reward
        if card.get('reward'):
            apply_reward(room_code, player_id, card['reward'])
        
        # Give new card
        new_card = generate_card()
        player['cards'].append(new_card)
        
        emit('solution_passed', {
            'playerId': player_id,
            'cardId': card_id,
            'testResults': result['testResults'],
            'newCard': new_card
        }, room=room_code)
        
        print(f'Player {player["username"]} passed {card["problem"]["title"]} in room {room_code}')
    else:
        emit('solution_failed', {
            'playerId': player_id,
            'cardId': card_id,
            'error': result['error'],
            'testResults': result['testResults']
        }, room=room_code)


@socketio.on('player_eliminated')
def handle_player_eliminated(data):
    """Player's timer hit 0."""
    socket_id = request.sid
    if socket_id not in socket_to_player: return
    
    player_id, room_code = socket_to_player[socket_id]
    room = get_room(room_code)
    if not room or player_id not in room['players']: return
    
    player = room['players'][player_id]
    if player['isEliminated']: return
    
    player['isEliminated'] = True
    player['eliminatedAt'] = time.time() * 1000
    player['timeRemaining'] = 0
    
    emit('player_eliminated', {
        'playerId': player_id,
        'username': player['username'],
        'eliminatedAt': player['eliminatedAt']
    }, room=room_code)
    
    print(f'Player {player["username"]} eliminated in room {room_code}')
    check_win_condition(room_code)


@socketio.on('apply_targeted_debuff')
def handle_apply_targeted_debuff(data):
    """Player selected target for debuff."""
    socket_id = request.sid
    if socket_id not in socket_to_player: return
    
    player_id, room_code = socket_to_player[socket_id]
    room = get_room(room_code)
    if not room: return
    
    target_id = data.get('targetPlayerId')
    player = room['players'].get(player_id)
    
    if not player or 'pendingTargetedReward' not in player:
        emit('error', {'message': 'No pending reward'})
        return
    
    if target_id not in room['players']:
        emit('error', {'message': 'Invalid target'})
        return
    
    target_player = room['players'][target_id]
    if target_player['isEliminated']:
        emit('error', {'message': 'Cannot target eliminated player'})
        return
    
    reward = player['pendingTargetedReward']
    
    if reward['effect'] == 'remove_time_targeted':
        room['players'][target_id]['timerEndTime'] = max(
            time.time() * 1000,
            room['players'][target_id]['timerEndTime'] - (reward['value'] * 1000)
        )
        
        emit('reward_applied', {
            'playerId': target_id,
            'effect': 'remove_time_targeted',
            'value': reward['value'],
            'fromPlayer': player_id,
            'targetName': target_player['username']
        }, room=room_code)
        
    elif reward['effect'] == 'flashbang_targeted':
        emit('flashbang_applied', {
            'fromPlayer': player_id,
            'fromUsername': player['username']
        }, room=target_player['socket_id'])
    
    player['pendingTargetedReward'] = None


@socketio.on('debug_trigger_reward')
def handle_debug_trigger_reward(data):
    """Dev tool to trigger rewards."""
    socket_id = request.sid
    if socket_id not in socket_to_player: return
    
    player_id, room_code = socket_to_player[socket_id]
    reward = data.get('reward')
    
    if reward:
        apply_reward(room_code, player_id, reward, is_debug=True)

@socketio.on('get_game_state')
def handle_get_game_state():
    """Request state refresh."""
    socket_id = request.sid
    if socket_id not in socket_to_player: return
    
    player_id, room_code = socket_to_player[socket_id]
    room = get_room(room_code)
    
    if room:
        emit('game_state', {
            'players': room['players'],
            'gameStatus': room['gameStatus'],
            'roomCode': room_code,
            'winner': room.get('winner')
        }, room=socket_id)

@socketio.on('test_message')
def handle_test_message(data):
    """Test message handler."""
    from_name = data.get('from', 'Unknown')
    message = data.get('message', '')
    if message:
        emit('test_message', {
            'from': from_name,
            'message': message
        }, broadcast=True, include_self=True)
