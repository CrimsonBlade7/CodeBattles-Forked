import { useEffect } from 'react'
import { useGameStore } from '../store/gameStore'

interface LobbyProps {
  emitStartGame: () => void
}

export function Lobby({ emitStartGame }: LobbyProps) {
  const { players, currentPlayerId, gameStatus, setGameStatus } = useGameStore()
  const playerList = Object.values(players)

  // Navigate to game screen when game starts
  useEffect(() => {
    if (gameStatus === 'playing') {
      // Navigation happens via App.tsx routing
    }
  }, [gameStatus])

  const handleStartGame = () => {
    emitStartGame()
  }

  const isHost = currentPlayerId && playerList.length > 0 && playerList[0].id === currentPlayerId

  return (
    <div className="min-h-screen bg-gray-900 text-white p-8">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-4xl font-bold mb-8 text-center">Game Lobby</h1>

        <div className="bg-gray-800 rounded-lg p-6 mb-6">
          <h2 className="text-2xl font-semibold mb-4">Players ({playerList.length})</h2>
          <div className="space-y-2">
            {playerList.map((player) => (
              <div
                key={player.id}
                className="flex items-center gap-3 p-3 bg-gray-700 rounded-lg"
              >
                <div className="w-3 h-3 bg-green-500 rounded-full"></div>
                <span className="font-medium">{player.username}</span>
                {player.id === currentPlayerId && (
                  <span className="text-xs text-blue-400">(You)</span>
                )}
              </div>
            ))}
          </div>
        </div>

        <div className="text-center">
          {isHost ? (
            <button
              onClick={handleStartGame}
              disabled={playerList.length < 1}
              className="px-8 py-4 bg-green-600 hover:bg-green-700 rounded-lg font-semibold text-lg disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              Start Game
            </button>
          ) : (
            <div className="text-gray-400">
              Waiting for host to start the game...
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
