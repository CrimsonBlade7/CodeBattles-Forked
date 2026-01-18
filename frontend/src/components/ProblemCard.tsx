import { ProblemCard as ProblemCardType } from '../store/gameStore'

interface ProblemCardProps {
  card: ProblemCardType
  isSelected: boolean
  onSelect: () => void
  index?: number
  isBurning?: boolean
  isNewCard?: boolean
}

export function ProblemCard({ card, isSelected, onSelect, index = 0, isBurning = false, isNewCard = false }: ProblemCardProps) {
  const difficultyColors = {
    Easy: 'bg-green-600',
    Medium: 'bg-yellow-600',
    Hard: 'bg-red-600'
  }

  return (
    <div
      className={`animate-float ${isBurning ? 'animate-burn' : ''} ${isNewCard ? 'animate-deal' : ''}`}
      style={{
        animationDelay: isNewCard ? '0s' : `${index * 0.2}s`
      }}
    >
      <div
        onClick={onSelect}
        className={`w-44 h-64 p-5 rounded-xl cursor-pointer transition-all duration-300 shadow-lg ${isSelected
          ? 'bg-gradient-to-br from-blue-50 to-blue-100 border-4 border-blue-500 scale-105 shadow-2xl -translate-y-4 rotate-2'
          : 'bg-gradient-to-br from-gray-50 to-white border-2 border-gray-300 hover:-translate-y-6 hover:rotate-3 hover:shadow-[0_25px_60px_rgba(0,_0,_0,_0.4)] hover:scale-105'
          }`}
        style={{
          transformStyle: 'preserve-3d'
        }}
      >
        <div className="flex flex-col h-full">
          <div className="flex items-start justify-between mb-3">
            <h3 className="font-bold text-base text-gray-900 leading-tight flex-1 mr-2">{card.problem.title}</h3>
            <span className={`px-2 py-1 rounded text-xs font-bold text-white whitespace-nowrap ${difficultyColors[card.problem.difficulty]}`}>
              {card.problem.difficulty}
            </span>
          </div>

          <p className="text-xs text-gray-700 mb-3 line-clamp-3 flex-1">
            {card.problem.description}
          </p>

          <div className="space-y-2">
            {card.reward && (
              <div className="flex items-center">
                <span className="text-xs px-2 py-1 bg-purple-100 text-purple-800 rounded-md font-medium border border-purple-200">
                  🎁 {card.reward.effect.replace('_', ' ')} {card.reward.value}s
                </span>
              </div>
            )}

            {card.challenge && (
              <div className="flex items-center">
                <span className="text-xs px-2 py-1 bg-orange-100 text-orange-800 rounded-md font-medium border border-orange-200">
                  ⚔️ {card.challenge.type.replace('_', ' ')} {card.challenge.value}
                </span>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}