"""
extensions.py

This file initializes "extensions" or plugins for our Flask application.
In this case, we are setting up SocketIO which allows real-time communication
between the server and the frontend.

We create the socketio object here but don't attach it to the app yet.
This prevents "circular import" errors where two files try to import each other.
"""

from flask_socketio import SocketIO

# Create the SocketIO instance.
# cors_allowed_origins="*" means we allow connections from any website (handy for development).
# async_mode='gevent' tells it to use the gevent library for better performance.
socketio = SocketIO(cors_allowed_origins="*", async_mode='gevent')
