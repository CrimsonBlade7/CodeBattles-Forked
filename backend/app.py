"""
app.py

This is the ENTRY POINT for the backend server.
When you run `python app.py`, this code executes.

It creates the Flask app and starts the server.
"""

import os
from src import create_app
from src.extensions import socketio

# Create the Flask application using our factory function
app = create_app()

# Only run if this file is executed directly (not imported)
if __name__ == '__main__':
    # Read configuration from environment variables (or use defaults)
    port = int(os.getenv('PORT', 5000))
    host = os.getenv('HOST', '0.0.0.0')  # 0.0.0.0 means "accept connections from any IP"
    
    print(f'Starting server on {host}:{port}')
    print(f'Connect frontend to: http://localhost:{port}')
    
    # Start the server!
    # socketio.run() wraps app.run() and adds WebSocket support
    socketio.run(app, host=host, port=port)