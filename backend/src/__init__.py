"""
__init__.py

This is the Package Initializer.
It tells Python that the folder 'src' is a package of modules that can be imported.

It also contains the 'create_app' function, which is the standard way to 
start a Flask application. It sets up the app, loads config, and connects plugins.
"""

from gevent import monkey
# Patch standard library to be async-compatible.
# This makes time.sleep(), socket operations, etc. work with gevent.
monkey.patch_all()

import os
from flask import Flask
from flask_cors import CORS
from .extensions import socketio

def create_app():
    """
    Factory function to create and configure the Flask application.
    """
    app = Flask(__name__)
    
    # 1. CONFIGURATION
    # Secret key is used for secure sessions (not strictly needed for this socket app but good practice)
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    
    # 2. SETUP CORS (Cross-Origin Resource Sharing)
    # Allows the frontend (running on port 5173) to talk to this backend (port 5000)
    CORS(app, resources={r"/*": {"origins": "*"}})
    
    # 3. INITIALIZE SOCKETIO
    # Connect the socketio plugin to this specific app instance
    socketio.init_app(app)
    
    # 4. REGISTER ROUTES & EVENTS
    # We import 'events' here so that the decorators (@socketio.on) run 
    # and register the event handlers.
    from . import events
    
    # Simple health check route
    @app.route('/')
    def index():
        from .game_state import game_state
        return {'status': 'CodeBattles Server Running', 'players': len(game_state['players'])}
        
    return app
