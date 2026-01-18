import { Player } from '../store/gameStore'

interface PlayerHealthBarProps {
  player: Player
  isCurrentPlayer: boolean
}

export function PlayerHealthBar({ player, isCurrentPlayer }: PlayerHealthBarProps) {
  // Calculate time remaining from timestamp
  const timeRemaining = player.timerEndTime
    ? Math.max(0, Math.floor((player.timerEndTime - Date.now()) / 1000))
    : 0
  const percentage = (timeRemaining / 300) * 100
  const currentCard = player.cards.find(c => c.id === player.currentProblem)

  return (
    <div className={`p-3 rounded-lg mb-2 ${isCurrentPlayer ? 'bg-blue-900/30 border border-blue-600' : 'bg-gray-800'}`}>
      <div className="flex items-center justify-between mb-1">
        <div className="flex items-center gap-2">
          <span className="font-semibold">{player.username}</span>
          {isCurrentPlayer && (
            <span className="text-xs text-blue-400">(You)</span>
          )}
        </div>
        <span className={`text-sm font-mono ${timeRemaining < 60 ? 'text-red-400' : 'text-gray-400'}`}>
          {Math.floor(timeRemaining / 60)}:{(Math.floor(timeRemaining % 60)).toString().padStart(2, '0')}
        </span>
      </div>

      <div className="w-full bg-gray-700 rounded-full h-3 mb-2">
        <div
          className={`h-3 rounded-full transition-all ${timeRemaining < 60
              ? 'bg-red-500'
              : timeRemaining < 120
                ? 'bg-yellow-500'
                : 'bg-green-500'
            }`}
          style={{ width: `${Math.max(0, percentage)}%` }}
        />
      </div>

      {currentCard && (
        <div className="text-xs text-gray-400 truncate">
          Working on: {currentCard.problem.title}
        </div>
      )}

      {player.isEliminated && (
        <div className="text-xs text-red-400 mt-1">Eliminated</div>
      )}
    </div>
  )
}