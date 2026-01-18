import eventlet
eventlet.monkey_patch()

import os
import uuid
import json
import subprocess
import time
from flask import Flask, request
from flask_socketio import SocketIO, emit
from flask_cors import CORS
from typing import Dict, List, Any, Optional

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')

# Enable CORS for all routes
CORS(app, resources={r"/*": {"origins": "*"}})

socketio = SocketIO(
    app,
    cors_allowed_origins="*",
    async_mode='eventlet'
)

# Socket ID to Player ID mapping
socket_to_player: Dict[str, str] = {}

# In-memory game state
game_state = {
    'players': {},
    'gameStatus': 'lobby',  # 'lobby' | 'playing' | 'ended'
    'roomCode': 'ROOM1',  # Single room system
    'winner': None
}

# Problem templates for card generation
PROBLEM_TEMPLATES = [
    {
        'problem': {
            'title': 'Two Sum',
            'description': 'Given an array of integers nums and an integer target, return indices of the two numbers such that they add up to target.',
            'difficulty': 'Easy',
            'functionSignature': 'def twoSum(nums: list, target: int) -> list:',
            'testCases': [
                {'input': {'nums': [2, 7, 11, 15], 'target': 9}, 'expectedOutput': [0, 1]},
                {'input': {'nums': [3, 2, 4], 'target': 6}, 'expectedOutput': [1, 2]},
                {'input': {'nums': [3, 3], 'target': 6}, 'expectedOutput': [0, 1]}
            ]
        },
        'reward': {'type': 'buff', 'target': 'self', 'effect': 'add_time', 'value': 30}
    },
    {
        'problem': {
            'title': 'Valid Parentheses',
            'description': 'Given a string s containing just the characters "(", ")", "{", "}", "[" and "]", determine if the input string is valid.',
            'difficulty': 'Easy',
            'functionSignature': 'def isValid(s: str) -> bool:',
            'testCases': [
                {'input': {'s': '()'}, 'expectedOutput': True},
                {'input': {'s': '()[]{}'}, 'expectedOutput': True},
                {'input': {'s': '(]'}, 'expectedOutput': False}
            ]
        },
        'reward': {'type': 'buff', 'target': 'self', 'effect': 'add_time', 'value': 25},
        'challenge': {'type': 'time_limit', 'value': 120}
    },
    {
        'problem': {
            'title': 'Merge Two Sorted Lists',
            'description': 'Merge two sorted linked lists and return it as a sorted list.',
            'difficulty': 'Easy',
            'functionSignature': 'def mergeTwoLists(list1: list, list2: list) -> list:',
            'testCases': [
                {'input': {'list1': [1, 2, 4], 'list2': [1, 3, 4]}, 'expectedOutput': [1, 1, 2, 3, 4, 4]},
                {'input': {'list1': [], 'list2': []}, 'expectedOutput': []}
            ]
        },
        'reward': {'type': 'debuff', 'target': 'other', 'effect': 'remove_time', 'value': 20}
    },
    {
        'problem': {
            'title': 'Longest Palindromic Substring',
            'description': 'Given a string s, return the longest palindromic substring in s.',
            'difficulty': 'Medium',
            'functionSignature': 'def longestPalindrome(s: str) -> str:',
            'testCases': [
                {'input': {'s': 'babad'}, 'expectedOutput': 'bab'},
                {'input': {'s': 'cbbd'}, 'expectedOutput': 'bb'}
            ]
        },
        'reward': {'type': 'buff', 'target': 'self', 'effect': 'add_time', 'value': 45},
        'challenge': {'type': 'complexity', 'value': 'O(n)'}
    },
    {
        'problem': {
            'title': 'Container With Most Water',
            'description': 'Find two lines that together with the x-axis forms a container, such that the container contains the most water.',
            'difficulty': 'Medium',
            'functionSignature': 'def maxArea(height: list) -> int:',
            'testCases': [
                {'input': {'height': [1, 8, 6, 2, 5, 4, 8, 3, 7]}, 'expectedOutput': 49},
                {'input': {'height': [1, 1]}, 'expectedOutput': 1}
            ]
        },
        'reward': {'type': 'debuff', 'target': 'all', 'effect': 'remove_time_all', 'value': 30}
    },
    {
        'problem': {
            'title': '3Sum',
            'description': 'Find all triplets in the array which gives the sum of zero.',
            'difficulty': 'Medium',
            'functionSignature': 'def threeSum(nums: list) -> list:',
            'testCases': [
                {'input': {'nums': [-1, 0, 1, 2, -1, -4]}, 'expectedOutput': [[-1, -1, 2], [-1, 0, 1]]},
                {'input': {'nums': []}, 'expectedOutput': []}
            ]
        },
        'reward': {'type': 'debuff', 'target': 'targeted', 'effect': 'remove_time_targeted', 'value': 50},
        'challenge': {'type': 'line_limit', 'value': 30}
    },
    {
        'problem': {
            'title': 'Trapping Rain Water',
            'description': 'Given n non-negative integers representing an elevation map, compute how much water it can trap after raining.',
            'difficulty': 'Hard',
            'functionSignature': 'def trap(height: list) -> int:',
            'testCases': [
                {'input': {'height': [0, 1, 0, 2, 1, 0, 1, 3, 2, 1, 2, 1]}, 'expectedOutput': 6},
                {'input': {'height': [4, 2, 0, 3, 2, 5]}, 'expectedOutput': 9}
            ]
        },
        'reward': {'type': 'buff', 'target': 'self', 'effect': 'add_time', 'value': 60}
    },
    {
        'problem': {
            'title': 'Longest Increasing Subsequence',
            'description': 'Find the length of the longest strictly increasing subsequence.',
            'difficulty': 'Hard',
            'functionSignature': 'def lengthOfLIS(nums: list) -> int:',
            'testCases': [
                {'input': {'nums': [10, 9, 2, 5, 3, 7, 101, 18]}, 'expectedOutput': 4},
                {'input': {'nums': [0, 1, 0, 3, 2, 3]}, 'expectedOutput': 4}
            ]
        },
        'reward': {'type': 'buff', 'target': 'self', 'effect': 'add_time', 'value': 45},
        'challenge': {'type': 'time_limit', 'value': 180}
    },
    {
        'problem': {
            'title': 'Binary Search',
            'description': 'Given a sorted array of integers and a target value, return the index of the target if found, otherwise return -1.',
            'difficulty': 'Medium',
            'functionSignature': 'def binarySearch(nums: list, target: int) -> int:',
            'testCases': [
                {'input': {'nums': [-1, 0, 3, 5, 9, 12], 'target': 9}, 'expectedOutput': 4},
                {'input': {'nums': [-1, 0, 3, 5, 9, 12], 'target': 2}, 'expectedOutput': -1},
                {'input': {'nums': [5], 'target': 5}, 'expectedOutput': 0}
            ]
        },
        'reward': {'type': 'debuff', 'target': 'targeted', 'effect': 'flashbang_targeted', 'value': 1}
    }
]


def generate_card() -> Dict[str, Any]:
    """Generate a random card from problem templates"""
    import random
    template = random.choice(PROBLEM_TEMPLATES).copy()
    card = {
        'id': str(uuid.uuid4()),
        'problem': template['problem'].copy(),
        'reward': template.get('reward'),
        'challenge': template.get('challenge')
    }
    return card


def execute_code(code: str, function_signature: str, test_cases: List[Dict]) -> Dict[str, Any]:
    """
    Execute Python code with test cases and return results.
    Returns: {
        'passed': bool,
        'testResults': List[Dict],
        'error': str | None
    }
    """
    # Debug mode: auto-pass if code contains debug marker
    if '# DEBUG: Auto-complete' in code:
        return {
            'passed': True,
            'testResults': [{'passed': True, 'input': 'DEBUG', 'expected': 'SKIP', 'actual': 'SKIP'}],
            'error': None
        }
    
    try:
        # Build the complete Python script
        script = f"""
{code}

# Test runner
import json
test_results = []
"""
        
        for i, test_case in enumerate(test_cases):
            input_dict = test_case['input']
            expected = test_case['expectedOutput']
            
            # Build function call from input
            function_name = function_signature.split('(')[0].replace('def ', '').strip()
            args_str = ', '.join([f"{k}={repr(v)}" for k, v in input_dict.items()])
            
            script += f"""
try:
    result_{i} = {function_name}({args_str})
    expected_{i} = {repr(expected)}
    passed_{i} = result_{i} == expected_{i}
    test_results.append({{
        'passed': passed_{i},
        'input': {json.dumps(input_dict)},
        'expected': expected_{i},
        'actual': result_{i}
    }})
except Exception as e:
    test_results.append({{
        'passed': False,
        'input': {json.dumps(input_dict)},
        'expected': {repr(expected)},
        'actual': None,
        'error': str(e)
    }})
"""
        
        script += """
print(json.dumps(test_results))
"""
        
        # Execute with subprocess
        process = subprocess.Popen(
            ['python3', '-c', script],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        stdout, stderr = process.communicate(timeout=10)
        
        if process.returncode != 0:
            return {
                'passed': False,
                'testResults': [],
                'error': stderr or 'Execution failed'
            }
        
        # Parse results
        try:
            test_results = json.loads(stdout.strip().split('\n')[-1])
            all_passed = all(t.get('passed', False) for t in test_results)
            return {
                'passed': all_passed,
                'testResults': test_results,
                'error': None
            }
        except json.JSONDecodeError:
            return {
                'passed': False,
                'testResults': [],
                'error': 'Could not parse test results'
            }
            
    except subprocess.TimeoutExpired:
        return {
            'passed': False,
            'testResults': [],
            'error': 'Code execution timed out (10 seconds max)'
        }
    except Exception as e:
        return {
            'passed': False,
            'testResults': [],
            'error': str(e)
        }


def apply_reward(player_id: str, reward: Dict[str, Any], is_debug: bool = False):
    """Apply reward to player(s)"""
    if reward['effect'] == 'add_time':
        if player_id in game_state['players']:
            # reward['value'] is in seconds, timerEndTime is in milliseconds
            game_state['players'][player_id]['timerEndTime'] += reward['value'] * 1000
            emit('reward_applied', {
                'playerId': player_id,
                'effect': 'add_time',
                'value': reward['value']
            }, broadcast=True)
    
    elif reward['effect'] == 'remove_time':
        # Select random other player
        candidates = [pid for pid in game_state['players'].keys() if not game_state['players'][pid]['isEliminated']]
        
        # In normal mode, exclude self. In debug mode, allow self if no others exist.
        other_players = [pid for pid in candidates if pid != player_id]
        
        if is_debug and not other_players and player_id in candidates:
            other_players = [player_id]
            print("Debug: Targeting self for remove_time")
            
        if other_players:
            import random
            target_id = random.choice(other_players)
            # reward['value'] is in seconds, timerEndTime is in milliseconds
            game_state['players'][target_id]['timerEndTime'] = max(
                time.time() * 1000,  # Current time in milliseconds
                game_state['players'][target_id]['timerEndTime'] - (reward['value'] * 1000)
            )
            emit('reward_applied', {
                'playerId': target_id,
                'effect': 'remove_time',
                'value': reward['value'],
                'fromPlayer': player_id
            }, broadcast=True)
    
    elif reward['effect'] == 'remove_time_targeted':
        # Request player to choose which opponent to target
        candidates = [pid for pid in game_state['players'].keys() if not game_state['players'][pid]['isEliminated']]
        other_players = [pid for pid in candidates if pid != player_id]
        
        if is_debug and not other_players and player_id in candidates:
            other_players = [player_id]
            
        if other_players:
            # Store pending reward in player state
            game_state['players'][player_id]['pendingTargetedReward'] = reward
            
            # Emit event to player requesting target selection
            emit('target_selection_required', {
                'effect': reward['effect'],
                'value': reward['value'],
                'availableTargets': [{
                    'playerId': pid,
                    'username': game_state['players'][pid]['username'],
                    'timeRemaining': max(0, int((game_state['players'][pid]['timerEndTime'] - time.time() * 1000) / 1000))
                } for pid in other_players]
            }, room=game_state['players'][player_id]['socket_id'])
            print(f'Sent target selection request to {game_state["players"][player_id]["username"]}')
    
    elif reward['effect'] == 'flashbang_targeted':
        # Request player to choose which opponent to flashbang
        candidates = [pid for pid in game_state['players'].keys() if not game_state['players'][pid]['isEliminated']]
        other_players = [pid for pid in candidates if pid != player_id]
        
        if is_debug and not other_players and player_id in candidates:
            other_players = [player_id]
            
        if other_players:
            # Store pending reward in player state
            game_state['players'][player_id]['pendingTargetedReward'] = reward
            
            # Emit event to player requesting target selection
            emit('target_selection_required', {
                'effect': reward['effect'],
                'value': reward['value'],
                'availableTargets': [{
                    'playerId': pid,
                    'username': game_state['players'][pid]['username'],
                    'timeRemaining': max(0, int((game_state['players'][pid]['timerEndTime'] - time.time() * 1000) / 1000))
                } for pid in other_players]
            }, room=game_state['players'][player_id]['socket_id'])
            print(f'Sent flashbang target selection request to {game_state["players"][player_id]["username"]}')
    
    elif reward['effect'] == 'remove_time_all':
        # Remove time from ALL other players
        candidates = [pid for pid in game_state['players'].keys() if not game_state['players'][pid]['isEliminated']]
        other_players = [pid for pid in candidates if pid != player_id]
        
        if is_debug and not other_players and player_id in candidates:
            other_players = [player_id]
            
        if other_players:
            affected_players = []
            for target_id in other_players:
                game_state['players'][target_id]['timerEndTime'] = max(
                    time.time() * 1000,
                    game_state['players'][target_id]['timerEndTime'] - (reward['value'] * 1000)
                )
                affected_players.append({
                    'playerId': target_id,
                    'username': game_state['players'][target_id]['username']
                })
        
        if affected_players:
            emit('reward_applied', {
                'effect': 'remove_time_all',
                'value': reward['value'],
                'fromPlayer': player_id,
                'affectedPlayers': affected_players
            }, broadcast=True)
            print(f'Applied remove_time_all: {reward["value"]}s from {len(affected_players)} players')




def check_win_condition():
    """Check if game should end (only 1 player remaining)"""
    active_players = [pid for pid, p in game_state['players'].items() 
                     if not p.get('isEliminated', False)]
    
    if len(active_players) == 1:
        game_state['gameStatus'] = 'ended'
        game_state['winner'] = active_players[0]
        emit('game_ended', {
            'winner': game_state['winner'],
            'winnerName': game_state['players'][active_players[0]]['username']
        }, broadcast=True)
        return True
    elif len(active_players) == 0:
        game_state['gameStatus'] = 'ended'
        emit('game_ended', {'winner': None}, broadcast=True)
        return True
    return False


@app.route('/')
def index():
    return {'status': 'CodeBattles Server Running', 'players': len(game_state['players'])}


@socketio.on('connect')
def handle_connect():
    print(f'Client connected: {request.sid}')
    emit('connected', {'socketId': request.sid})


@socketio.on('disconnect')
def handle_disconnect():
    socket_id = request.sid
    print(f'Client disconnected: {socket_id}')
    
    # Find and remove player
    if socket_id in socket_to_player:
        player_id = socket_to_player[socket_id]
        if player_id in game_state['players']:
            player_name = game_state['players'][player_id]['username']
            del game_state['players'][player_id]
            emit('player_left', {
                'playerId': player_id,
                'username': player_name
            }, broadcast=True)
        
        del socket_to_player[socket_id]
        
        # Check win condition
        check_win_condition()


@socketio.on('join_room')
def handle_join_room(data):
    """Handle player joining a room"""
    username = data.get('username', '').strip()
    room_code = data.get('roomCode', 'ROOM1').strip()
    
    if not username:
        emit('join_error', {'message': 'Username required'})
        return
    
    socket_id = request.sid
    
    # Generate player ID
    player_id = str(uuid.uuid4())
    
    # Map socket to player
    socket_to_player[socket_id] = player_id
    
    # Create player
    player = {
        'id': player_id,
        'username': username,
        'socket_id': socket_id,
        'timerEndTime': None,  # Will be set when game starts
        'isEliminated': False,
        'eliminatedAt': None,  # Timestamp when player was eliminated
        'currentProblem': None,
        'cards': [],
        'isTimeFrozen': False,
        'frozenUntil': None
    }
    
    game_state['players'][player_id] = player
    
    # Broadcast to all clients
    emit('player_joined', {
        'playerId': player_id,
        'username': username
    }, broadcast=True)
    
    # Send current game state to new player
    emit('game_state', game_state, room=socket_id)
    
    print(f'Player {username} ({player_id}) joined room {room_code}')


@socketio.on('start_game')
def handle_start_game():
    """Handle game start - deal cards to all players"""
    socket_id = request.sid
    
    if socket_id not in socket_to_player:
        emit('error', {'message': 'Not connected'})
        return
    
    player_id = socket_to_player[socket_id]
    
    # Check if player is first player (host)
    if len(game_state['players']) == 0:
        emit('error', {'message': 'No players in game'})
        return
    
    first_player_id = list(game_state['players'].keys())[0]
    if player_id != first_player_id:
        emit('error', {'message': 'Only host can start game'})
        return
    
    # Set game status
    game_state['gameStatus'] = 'playing'
    
    # Set timer end time for all players (5 minutes from now, in milliseconds)
    timer_end_time = (time.time() + 300) * 1000  # Convert to milliseconds for JS
    for pid in game_state['players'].keys():
        game_state['players'][pid]['timerEndTime'] = timer_end_time
    
    # Deal 5 cards to each player
    for pid in game_state['players'].keys():
        cards = [generate_card() for _ in range(5)]
        game_state['players'][pid]['cards'] = cards
    
    # Broadcast game started
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


@socketio.on('select_card')
def handle_select_card(data):
    """Handle player selecting a problem card"""
    socket_id = request.sid
    
    if socket_id not in socket_to_player:
        emit('error', {'message': 'Not connected'})
        return
    
    player_id = socket_to_player[socket_id]
    card_id = data.get('cardId')
    
    if player_id not in game_state['players']:
        emit('error', {'message': 'Player not found'})
        return
    
    player = game_state['players'][player_id]
    
    # Verify player owns the card
    card = next((c for c in player['cards'] if c['id'] == card_id), None)
    if not card:
        emit('error', {'message': 'Card not found in player hand'})
        return
    
    # Update current problem
    player['currentProblem'] = card_id
    
    # Broadcast to all clients
    emit('card_selected', {
        'playerId': player_id,
        'cardId': card_id,
        'problem': card['problem']
    }, broadcast=True)
    
    print(f'Player {player["username"]} selected card {card_id}')


@socketio.on('submit_solution')
def handle_submit_solution(data):
    """Handle solution submission and code execution"""
    socket_id = request.sid
    
    if socket_id not in socket_to_player:
        emit('error', {'message': 'Not connected'})
        return
    
    player_id = socket_to_player[socket_id]
    card_id = data.get('cardId')
    code = data.get('code', '')
    
    if player_id not in game_state['players']:
        emit('error', {'message': 'Player not found'})
        return
    
    player = game_state['players'][player_id]
    
    # Verify player is not eliminated
    if player['isEliminated']:
        emit('error', {'message': 'Player is eliminated'})
        return
    
    # Find the card
    card = next((c for c in player['cards'] if c['id'] == card_id), None)
    if not card:
        emit('error', {'message': 'Card not found'})
        return
    
    if player['currentProblem'] != card_id:
        emit('error', {'message': 'Card is not currently selected'})
        return
    
    # Execute code
    function_signature = card['problem']['functionSignature']
    test_cases = card['problem']['testCases']
    
    result = execute_code(code, function_signature, test_cases)
    
    if result['passed']:
        # Remove card from hand
        player['cards'] = [c for c in player['cards'] if c['id'] != card_id]
        player['currentProblem'] = None
        
        # Apply reward if exists
        if card.get('reward'):
            apply_reward(player_id, card['reward'])
        
        # Generate new card
        new_card = generate_card()
        player['cards'].append(new_card)
        
        # Broadcast success
        emit('solution_passed', {
            'playerId': player_id,
            'cardId': card_id,
            'testResults': result['testResults'],
            'newCard': new_card
        }, broadcast=True)
        
        print(f'Player {player["username"]} passed problem {card["problem"]["title"]}')
    else:
        # Broadcast failure
        emit('solution_failed', {
            'playerId': player_id,
            'cardId': card_id,
            'error': result['error'],
            'testResults': result['testResults']
        }, broadcast=True)
        
        print(f'Player {player["username"]} failed problem {card["problem"]["title"]}')


@socketio.on('player_eliminated')
def handle_player_eliminated(data):
    """Handle player elimination (when timer reaches 0)"""
    socket_id = request.sid
    
    if socket_id not in socket_to_player:
        emit('error', {'message': 'Not connected'})
        return
    
    player_id = socket_to_player[socket_id]
    
    if player_id not in game_state['players']:
        emit('error', {'message': 'Player not found'})
        return
    
    player = game_state['players'][player_id]
    
    if player['isEliminated']:
        return  # Already eliminated
    
    # Mark as eliminated
    player['isEliminated'] = True
    player['eliminatedAt'] = time.time() * 1000  # Timestamp in milliseconds
    player['timeRemaining'] = 0
    
    # Broadcast elimination
    emit('player_eliminated', {
        'playerId': player_id,
        'username': player['username'],
        'eliminatedAt': player['eliminatedAt']
    }, broadcast=True)
    
    print(f'Player {player["username"]} eliminated')
    
    # Check win condition
    check_win_condition()

@socketio.on('apply_targeted_debuff')
def handle_apply_targeted_debuff(data):
    """Handle player selection for targeted debuff"""
    socket_id = request.sid
    
    if socket_id not in socket_to_player:
        emit('error', {'message': 'Not connected'})
        return
    
    player_id = socket_to_player[socket_id]
    target_id = data.get('targetPlayerId')
    
    if player_id not in game_state['players']:
        emit('error', {'message': 'Player not found'})
        return
    
    player = game_state['players'][player_id]
    
    # Check if player has a pending targeted reward
    if 'pendingTargetedReward' not in player or not player['pendingTargetedReward']:
        emit('error', {'message': 'No pending targeted reward'})
        return
    
    # Validate target is a valid opponent
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
    
    
    # Apply the debuff based on effect type
    reward = player['pendingTargetedReward']
    
    if reward['effect'] == 'remove_time_targeted':
        # Apply time removal
        game_state['players'][target_id]['timerEndTime'] = max(
            time.time() * 1000,
            game_state['players'][target_id]['timerEndTime'] - (reward['value'] * 1000)
        )
        
        # Broadcast the reward application
        emit('reward_applied', {
            'playerId': target_id,
            'effect': 'remove_time_targeted',
            'value': reward['value'],
            'fromPlayer': player_id,
            'targetName': game_state['players'][target_id]['username']
        }, broadcast=True)
        
        print(f'Player {player["username"]} targeted {target_player["username"]} with {reward["value"]}s debuff')
    
    elif reward['effect'] == 'flashbang_targeted':
        # Apply flashbang to target player only
        emit('flashbang_applied', {
            'fromPlayer': player_id,
            'fromUsername': player['username']
        }, room=target_player['socket_id'])
        
        print(f'Player {player["username"]} flashbanged {target_player["username"]}')
    
    # Clear pending reward
    player['pendingTargetedReward'] = None


@socketio.on('debug_trigger_reward')
def handle_debug_trigger_reward(data):
    """Handle debug reward trigger"""
    socket_id = request.sid
    
    if socket_id not in socket_to_player:
        return
        
    player_id = socket_to_player[socket_id]
    reward = data.get('reward')
    
    if player_id in game_state['players'] and reward:
        print(f'Debug reward triggered by {game_state["players"][player_id]["username"]}: {reward["effect"]}')
        apply_reward(player_id, reward, is_debug=True)



@socketio.on('get_game_state')
def handle_get_game_state():
    """Send current game state to requesting client"""
    socket_id = request.sid
    emit('game_state', game_state, room=socket_id)


@socketio.on('test_message')
def handle_test_message(data):
    """Handle test messages for connection testing"""
    from_name = data.get('from', 'Unknown')
    message = data.get('message', '')
    
    if message:
        emit('test_message', {
            'from': from_name,
            'message': message
        }, broadcast=True, include_self=True)
        
        print(f'Test message from {from_name}: {message}')


if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    host = os.getenv('HOST', '0.0.0.0')
    
    print(f'Starting server on {host}:{port}')
    print(f'Connect frontend to: http://localhost:{port}')
    print(f'For ngrok: Use the ngrok URL when running ngrok http {port}')
    
    socketio.run(app, host=host, port=port)