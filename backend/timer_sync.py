

@socketio.on('update_timer')
def handle_update_timer(data):
    """Handle timer updates from clients"""
    socket_id = request.sid
    
    if socket_id not in socket_to_player:
        return
    
    player_id = socket_to_player[socket_id]
    time_remaining = data.get('timeRemaining', 0)
    
    if player_id in game_state['players']:
        game_state['players'][player_id]['timeRemaining'] = time_remaining
        
        # Broadcast to other players
        emit('timer_update', {
            'playerId': player_id,
            'timeRemaining': time_remaining
        }, broadcast=True, include_self=False)


