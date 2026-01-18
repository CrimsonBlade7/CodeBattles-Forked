# CodeBattles - Multiplayer Game

A real-time multiplayer game built with React (Vite) frontend and Flask backend using Socket.IO for real-time communication.

## Tech Stack

### Frontend
- **React** (via Vite): Fast development server and build tool
- **Tailwind CSS**: Utility-first CSS framework
- **Zustand**: Lightweight global state management
- **Socket.io-client**: Real-time WebSocket communication

### Backend
- **Python Flask**: Lightweight web framework
- **Flask-SocketIO**: WebSocket support for Flask
- **In-memory state**: No database needed for demo

### Networking
- **Local IP (0.0.0.0)**: Connect devices on same Wi-Fi network
- **Ngrok**: Public tunnel for remote access when local network isn't available

## Setup Instructions

### Prerequisites

- **Node.js** (v18 or higher) - [Download](https://nodejs.org/)
- **Python** (v3.8 or higher) - [Download](https://www.python.org/)
- **Ngrok** (optional) - [Download](https://ngrok.com/download)

### Frontend Setup

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Create a `.env` file (optional, defaults to `http://localhost:5000`):
   ```bash
   cp .env.example .env
   ```
   Edit `.env` and set `VITE_SOCKET_URL` to your backend URL if needed.

4. Start the development server:
   ```bash
   npm run dev
   ```

   The frontend will be available at `http://localhost:5173`

### Backend Setup

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```

2. Create a virtual environment (recommended):
   ```bash
   python -m venv venv
   
   # On macOS/Linux:
   source venv/bin/activate
   
   # On Windows:
   venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Create a `.env` file (optional, defaults are fine for local development):
   ```bash
   cp .env.example .env
   ```

5. Start the Flask server:
   ```bash
   python app.py
   ```

   The backend will be available at `http://localhost:5000` (or `http://0.0.0.0:5000` for network access)

## Running the Application

### Local Development

1. Start the backend server (in `backend/` directory):
   ```bash
   python app.py
   ```

2. Start the frontend server (in `frontend/` directory):
   ```bash
   npm run dev
   ```

3. Open your browser to `http://localhost:5173`

### Network Access (Same Wi-Fi)

The backend server is configured to listen on `0.0.0.0:5000`, which means it accepts connections from any device on your local network.

1. Find your computer's local IP address:
   - **macOS/Linux**: Run `ifconfig` or `ip addr show`
   - **Windows**: Run `ipconfig`

2. Update the frontend `.env` file:
   ```
   VITE_SOCKET_URL=http://YOUR_LOCAL_IP:5000
   ```

3. Team members can access:
   - Frontend: `http://YOUR_LOCAL_IP:5173` (if you configure Vite to allow network access)
   - Or each person runs the frontend locally and just connects to your backend IP

### Using Ngrok (Remote Access)

If local network access isn't working or you need remote access:

1. **Install Ngrok**: Download from [ngrok.com](https://ngrok.com/download) and add to your PATH

2. **Start your backend server** (if not already running):
   ```bash
   cd backend
   python app.py
   ```

3. **In a new terminal, start ngrok**:
   ```bash
   ngrok http 5000
   ```

4. **Copy the ngrok HTTPS URL** (looks like `https://abc123.ngrok.io`)

5. **Update frontend `.env`**:
   ```
   VITE_SOCKET_URL=https://YOUR_NGROK_URL
   ```
   Replace `YOUR_NGROK_URL` with your actual ngrok URL (e.g., `https://abc123.ngrok.io`)

6. **Restart the frontend** to pick up the new environment variable

7. **Share the ngrok URL** with your team members - they should update their `.env` files too

**Note**: Free ngrok URLs change each time you restart ngrok. For a stable URL, consider ngrok's paid plans.

## Project Structure

```
CodeBattles-nwHacks2026/
├── frontend/
│   ├── src/
│   │   ├── store/
│   │   │   └── gameStore.ts      # Zustand store for game state
│   │   ├── hooks/
│   │   │   └── useSocket.ts      # Socket.io connection hook
│   │   ├── App.tsx               # Main app component
│   │   ├── main.tsx              # React entry point
│   │   └── index.css             # Tailwind styles
│   ├── package.json
│   ├── vite.config.ts
│   └── tailwind.config.js
├── backend/
│   ├── app.py                    # Flask app with Socket.IO
│   └── requirements.txt
└── README.md
```

## Socket.IO Events

### Client → Server

- `player_move`: Send player position update
  ```javascript
  { playerId: 1, position: { x: 100, y: 200 } }
  ```

- `player_action`: Send player action
  ```javascript
  { playerId: 1, action: 'jump' }
  ```

- `get_game_state`: Request current game state

### Server → Client

- `player_move`: Broadcast player position to all clients
- `player_action`: Broadcast player action to all clients
- `game_state`: Send full game state (on connect or request)
- `connect`: Connection established
- `disconnect`: Connection lost

## Development Tips

- **Hot Reload**: Both frontend (Vite) and backend (Flask debug mode) support hot reload
- **State Management**: Player positions/actions are stored in Zustand store and synced via Socket.IO
- **CORS**: Backend has CORS enabled for all origins (adjust in production)
- **Debugging**: Check browser console and terminal for Socket.IO connection status

## Troubleshooting

### Frontend can't connect to backend
- Verify backend is running on port 5000
- Check `VITE_SOCKET_URL` in `.env` matches your backend URL
- Ensure CORS is enabled on backend (already configured)
- Check firewall settings if using local IP

### Ngrok connection issues
- Make sure backend is running before starting ngrok
- Use HTTPS URL from ngrok (not HTTP)
- Update `.env` file and restart frontend after changing URL

### Multiple players not syncing
- Verify all clients are connected to the same backend URL
- Check browser console for Socket.IO errors
- Ensure `broadcast=True` in backend event handlers

## License

MIT