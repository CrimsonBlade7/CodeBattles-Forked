"""
events.py

This file handles all the network events.
When a player sends a message (like "join_room" or "submit_solution"),
the corresponding function in this file is called.
"""

import time
import uuid
from flask import request
from flask_socketio import emit

# Import from our other modules
from .extensions import socketio
from .game_state import (
    game_state, socket_to_player, 
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
    emit('connected', {'socketId': request.sid})

@socketio.on('disconnect')
def handle_disconnect():
    """Called when a client drops connection."""
    socket_id = request.sid
    print(f'Client disconnected: {socket_id}')
    
    # 1. Clean up player data
    if socket_id in socket_to_player:
        player_id = socket_to_player[socket_id]
        if player_id in game_state['players']:
            player_name = game_state['players'][player_id]['username']
            del game_state['players'][player_id]
            
            # Tell others they left
            emit('player_left', {
                'playerId': player_id,
                'username': player_name
            }, broadcast=True)
        
        del socket_to_player[socket_id]
        
        # Check if the game is over because everyone left
        check_win_condition()

# --------------------------
# GAME LOBBY EVENTS
# --------------------------

@socketio.on('join_room')
def handle_join_room(data):
    """
    Player wants to join the game.
    We create a player object for them and add it to our state.
    """
    username = data.get('username', '').strip()
    room_code = data.get('roomCode', 'ROOM1').strip()
    
    if not username:
        emit('join_error', {'message': 'Username required'})
        return
    
    socket_id = request.sid
    
    # Create a unique ID for the player
    player_id = str(uuid.uuid4())
    socket_to_player[socket_id] = player_id
    
    # Initialize player stats
    player = {
        'id': player_id,
        'username': username,
        'socket_id': socket_id,
        'timerEndTime': None,  # Will be set when game starts
        'isEliminated': False,
        'eliminatedAt': None,
        'currentProblem': None,
        'cards': [],
        'isTimeFrozen': False,
        'frozenUntil': None
    }
    
    game_state['players'][player_id] = player
    
    # Tell everyone a new player arrived
    emit('player_joined', {
        'playerId': player_id,
        'username': username
    }, broadcast=True)
    
    # Send the current game state to the new player so they know what's happening
    emit('game_state', game_state, room=socket_id)
    
    print(f'Player {username} ({player_id}) joined room {room_code}')


@socketio.on('start_game')
def handle_start_game():
    """
    Host clicked "Start Game".
    We prepare the game by giving everyone cards and setting the timer.
    """
    socket_id = request.sid
    
    # Validation: Ensure connected and host
    if socket_id not in socket_to_player:
        emit('error', {'message': 'Not connected'})
        return
    
    player_id = socket_to_player[socket_id]
    
    if not game_state['players']:
        emit('error', {'message': 'No players in game'})
        return
    
    # First player in the list is the host
    first_player_id = list(game_state['players'].keys())[0]
    if player_id != first_player_id:
        emit('error', {'message': 'Only host can start game'})
        return
    
    # Status update
    game_state['gameStatus'] = 'playing'
    
    # Set timer: 5 minutes from now
    timer_end_time = (time.time() + 300) * 1000  # JS uses milliseconds
    for pid in game_state['players'].keys():
        game_state['players'][pid]['timerEndTime'] = timer_end_time
    
    # Deal 5 cards to each player
    for pid in game_state['players'].keys():
        cards = [generate_card() for _ in range(5)]
        game_state['players'][pid]['cards'] = cards
    
    # Broadcast start
    # We construct a slightly cleaner object to send (sanitizing if needed)
    emit('game_started', {
        'players': {pid: {
            'id': p['id'],
            'username': p['username'],
            'timerEndTime': p['timerEndTime'],
            'isEliminated': p['isEliminated'],
            'eliminatedAt': p.get('eliminatedAt'),
            'currentProblem': p['currentProblem'],
            'cards': p['cards']
        } for pid, p in game_state['players'].items()}
    }, broadcast=True)
    
    print(f'Game started by {game_state["players"][player_id]["username"]}')

# --------------------------
# GAMEPLAY EVENTS
# --------------------------

@socketio.on('select_card')
def handle_select_card(data):
    """Player clicked on a card to work on."""
    socket_id = request.sid
    if socket_id not in socket_to_player: return
    
    player_id = socket_to_player[socket_id]
    card_id = data.get('cardId')
    
    if player_id not in game_state['players']: return
    
    player = game_state['players'][player_id]
    
    # Verify card ownership
    card = next((c for c in player['cards'] if c['id'] == card_id), None)
    if not card:
        emit('error', {'message': 'Card not found in player hand'})
        return
    
    player['currentProblem'] = card_id
    
    # Tell others (maybe to show what they are working on)
    emit('card_selected', {
        'playerId': player_id,
        'cardId': card_id,
        'problem': card['problem']
    }, broadcast=True)
    
    print(f'Player {player["username"]} selected card {card_id}')


@socketio.on('submit_solution')
def handle_submit_solution(data):
    """
    Player submitted code.
    We run it securely and return the result.
    """
    socket_id = request.sid
    if socket_id not in socket_to_player: return
    
    player_id = socket_to_player[socket_id]
    card_id = data.get('cardId')
    code = data.get('code', '')
    
    if player_id not in game_state['players']: return
    player = game_state['players'][player_id]
    
    if player['isEliminated']:
        emit('error', {'message': 'Player is eliminated'})
        return
    
    # Find card
    card = next((c for c in player['cards'] if c['id'] == card_id), None)
    if not card:
        emit('error', {'message': 'Card not found'})
        return
    
    if player['currentProblem'] != card_id:
        emit('error', {'message': 'Card is not currently selected'})
        return
    
    # Run the code!
    function_signature = card['problem']['functionSignature']
    test_cases = card['problem']['testCases']
    result = execute_code(code, function_signature, test_cases)
    
    if result['passed']:
        # SUCCESS!
        # 1. Remove used card
        player['cards'] = [c for c in player['cards'] if c['id'] != card_id]
        player['currentProblem'] = None
        
        # 2. Apply Reward
        if card.get('reward'):
            apply_reward(player_id, card['reward'])
        
        # 3. Give new card
        new_card = generate_card()
        player['cards'].append(new_card)
        
        emit('solution_passed', {
            'playerId': player_id,
            'cardId': card_id,
            'testResults': result['testResults'],
            'newCard': new_card
        }, broadcast=True)
        
        print(f'Player {player["username"]} passed problem {card["problem"]["title"]}')
    else:
        # FAIL
        emit('solution_failed', {
            'playerId': player_id,
            'cardId': card_id,
            'error': result['error'],
            'testResults': result['testResults']
        }, broadcast=True)
        
        print(f'Player {player["username"]} failed problem {card["problem"]["title"]}')


@socketio.on('player_eliminated')
def handle_player_eliminated(data):
    """Client says their timer hit 0."""
    socket_id = request.sid
    if socket_id not in socket_to_player: return
    
    player_id = socket_to_player[socket_id]
    player = game_state['players'][player_id]
    
    if player['isEliminated']: return
    
    player['isEliminated'] = True
    player['eliminatedAt'] = time.time() * 1000
    player['timeRemaining'] = 0
    
    emit('player_eliminated', {
        'playerId': player_id,
        'username': player['username'],
        'eliminatedAt': player['eliminatedAt']
    }, broadcast=True)
    
    print(f'Player {player["username"]} eliminated')
    check_win_condition()


@socketio.on('apply_targeted_debuff')
def handle_apply_targeted_debuff(data):
    """
    Player chose a target for their reward/attack.
    """
    socket_id = request.sid
    if socket_id not in socket_to_player: return
    
    player_id = socket_to_player[socket_id]
    target_id = data.get('targetPlayerId')
    
    player = game_state['players'][player_id]
    
    # Validation
    if 'pendingTargetedReward' not in player or not player['pendingTargetedReward']:
        emit('error', {'message': 'No pending targeted reward'})
        return
        
    if target_id not in game_state['players']:
        emit('error', {'message': 'Invalid target player'})
        return
        
    target_player = game_state['players'][target_id]
    
    if target_id == player_id:
        emit('error', {'message': 'Cannot target yourself'})
        return
        
    if target_player['isEliminated']:
        emit('error', {'message': 'Cannot target eliminated player'})
        return
    
    # Execute the attack
    reward = player['pendingTargetedReward']
    
    if reward['effect'] == 'remove_time_targeted':
        game_state['players'][target_id]['timerEndTime'] = max(
            time.time() * 1000,
            game_state['players'][target_id]['timerEndTime'] - (reward['value'] * 1000)
        )
        
        emit('reward_applied', {
            'playerId': target_id,
            'effect': 'remove_time_targeted',
            'value': reward['value'],
            'fromPlayer': player_id,
            'targetName': game_state['players'][target_id]['username']
        }, broadcast=True)
        print(f'Player {player["username"]} targeted {target_player["username"]} with {reward["value"]}s debuff')
        
    elif reward['effect'] == 'flashbang_targeted':
        emit('flashbang_applied', {
            'fromPlayer': player_id,
            'fromUsername': player['username']
        }, room=target_player['socket_id'])
        print(f'Player {player["username"]} flashbanged {target_player["username"]}')
    
    # Clear pending
    player['pendingTargetedReward'] = None


@socketio.on('debug_trigger_reward')
def handle_debug_trigger_reward(data):
    """Dev tool to manually trigger events."""
    socket_id = request.sid
    if socket_id not in socket_to_player: return
    player_id = socket_to_player[socket_id]
    reward = data.get('reward')
    if player_id in game_state['players'] and reward:
        print(f'Debug reward triggered by {game_state["players"][player_id]["username"]}: {reward["effect"]}')
        apply_reward(player_id, reward, is_debug=True)

@socketio.on('get_game_state')
def handle_get_game_state():
    """Request refresh of state."""
    socket_id = request.sid
    emit('game_state', game_state, room=socket_id)

@socketio.on('test_message')
def handle_test_message(data):
    """Ping pong."""
    from_name = data.get('from', 'Unknown')
    message = data.get('message', '')
    if message:
        emit('test_message', {
            'from': from_name,
            'message': message
        }, broadcast=True, include_self=True)
        print(f'Test message from {from_name}: {message}')
