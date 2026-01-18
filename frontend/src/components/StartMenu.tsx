import { useState, useEffect } from 'react'
import { useGameStore } from '../store/gameStore'

interface StartMenuProps {
  emitJoinRoom: (username: string, roomCode: string) => void
  connected: boolean
}

export function StartMenu({ emitJoinRoom, connected }: StartMenuProps) {
  const [username, setUsername] = useState('')
  const [roomCode, setRoomCode] = useState('')
  const { setUsername: setStoreUsername, joinRoom, gameStatus } = useGameStore()

  // Navigate to lobby when gameStatus changes to 'lobby'
  useEffect(() => {
    if (gameStatus === 'lobby') {
      // Navigation happens via App.tsx routing
    }
  }, [gameStatus])

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (username.trim() && connected) {
      setStoreUsername(username.trim())
      const finalRoomCode = roomCode.trim() || 'ROOM1'
      joinRoom(finalRoomCode)
      // Emit join_room event to backend
      emitJoinRoom(username.trim(), finalRoomCode)
    }
  }

  return (
    <div className="min-h-screen bg-gray-900 text-white flex items-center justify-center">
      <div className="max-w-md w-full p-8">
        <div className="text-center mb-8">
          <h1 className="text-5xl font-bold mb-2 bg-gradient-to-r from-blue-400 to-purple-600 bg-clip-text text-transparent">
            CodeBattles
          </h1>
          <p className="text-gray-400">LeetCode Party Game</p>
        </div>

        <form onSubmit={handleSubmit} className="bg-gray-800 rounded-lg p-6 space-y-6">
          <div>
            <label htmlFor="username" className="block text-sm font-medium mb-2">
              Username
            </label>
            <input
              id="username"
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="Enter your username"
              required
              disabled={!connected}
              className="w-full px-4 py-3 bg-gray-700 border border-gray-600 rounded-lg focus:outline-none focus:border-blue-500 text-white disabled:opacity-50"
            />
          </div>

          <div>
            <label htmlFor="roomCode" className="block text-sm font-medium mb-2">
              Room Code (any code works)
            </label>
            <input
              id="roomCode"
              type="text"
              value={roomCode}
              onChange={(e) => setRoomCode(e.target.value.toUpperCase())}
              placeholder="Enter room code"
              disabled={!connected}
              className="w-full px-4 py-3 bg-gray-700 border border-gray-600 rounded-lg focus:outline-none focus:border-blue-500 text-white disabled:opacity-50"
            />
          </div>

          {!connected && (
            <div className="text-red-400 text-sm text-center">
              Connecting to server...
            </div>
          )}

          <button
            type="submit"
            disabled={!connected || !username.trim()}
            className="w-full py-3 bg-blue-600 hover:bg-blue-700 rounded-lg font-semibold transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Join Game
          </button>
        </form>
      </div>
    </div>
  )
}
