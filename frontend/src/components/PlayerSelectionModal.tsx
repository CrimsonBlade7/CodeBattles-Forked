
interface TargetPlayer {
    playerId: string
    username: string
    timeRemaining: number
}

interface PlayerSelectionModalProps {
    targets: TargetPlayer[]
    rewardValue: number
    onSelect: (targetId: string) => void
}

export function PlayerSelectionModal({ targets, rewardValue, onSelect }: PlayerSelectionModalProps) {
    return (
        <div className="fixed inset-0 flex items-center justify-center z-50 bg-black/50">
            <div className="bg-gray-800 text-white rounded-xl p-8 max-w-md w-full mx-4 shadow-2xl border-2 border-purple-500">
                <div className="text-center mb-6">
                    <h2 className="text-3xl font-bold mb-2">Choose Your Target</h2>
                    <p className="text-gray-300">
                        Remove <span className="text-red-400 font-bold">{rewardValue} seconds</span> from an opponent
                    </p>
                </div>

                <div className="space-y-3">
                    {targets.map((target) => (
                        <button
                            key={target.playerId}
                            onClick={() => onSelect(target.playerId)}
                            className="w-full bg-gradient-to-r from-gray-700 to-gray-600 hover:from-purple-600 hover:to-purple-500 
                         p-4 rounded-lg transition-all duration-200 hover:scale-105 hover:shadow-xl
                         border-2 border-gray-600 hover:border-purple-400"
                        >
                            <div className="flex justify-between items-center">
                                <div className="flex flex-col items-start">
                                    <span className="text-xl font-bold">{target.username}</span>
                                    <span className="text-sm text-gray-400">
                                        Time Remaining: {Math.floor(target.timeRemaining / 60)}:{String(target.timeRemaining % 60).padStart(2, '0')}
                                    </span>
                                </div>
                                <div className="text-2xl">🎯</div>
                            </div>
                        </button>
                    ))}
                </div>

                <p className="text-sm text-gray-400 text-center mt-6">
                    Click on a player to target them
                </p>
            </div>
        </div>
    )
}
