interface DebugMenuProps {
    onTriggerReward: (rewardType: string) => void
    onClose: () => void
}

export function DebugMenu({ onTriggerReward, onClose }: DebugMenuProps) {
    return (
        <div className="fixed bottom-16 right-4 bg-gray-800 border-2 border-purple-500 rounded-lg p-4 shadow-2xl z-50 max-w-xs">
            <div className="flex justify-between items-center mb-3">
                <h3 className="text-lg font-bold text-purple-400">🐛 Debug Menu</h3>
                <button
                    onClick={onClose}
                    className="text-gray-400 hover:text-white transition-colors text-xl font-bold px-2"
                >
                    ×
                </button>
            </div>
            <div className="space-y-2">
                <button
                    onClick={() => onTriggerReward('add_time')}
                    className="w-full px-3 py-2 bg-green-600 hover:bg-green-700 rounded text-sm font-semibold transition-colors"
                >
                    ➕ Add Time (Self)
                </button>

                <button
                    onClick={() => onTriggerReward('remove_time')}
                    className="w-full px-3 py-2 bg-orange-600 hover:bg-orange-700 rounded text-sm font-semibold transition-colors"
                >
                    ➖ Remove Time (Random)
                </button>

                <button
                    onClick={() => onTriggerReward('remove_time_targeted')}
                    className="w-full px-3 py-2 bg-red-600 hover:bg-red-700 rounded text-sm font-semibold transition-colors"
                >
                    🎯 Remove Time (Targeted)
                </button>

                <button
                    onClick={() => onTriggerReward('remove_time_all')}
                    className="w-full px-3 py-2 bg-red-800 hover:bg-red-900 rounded text-sm font-semibold transition-colors"
                >
                    💥 Remove Time (All)
                </button>

                <button
                    onClick={() => onTriggerReward('flashbang_targeted')}
                    className="w-full px-3 py-2 bg-yellow-500 hover:bg-yellow-600 rounded text-sm font-semibold transition-colors text-black"
                >
                    💡 Flashbang (Targeted)
                </button>

                <button
                    onClick={() => onTriggerReward('flashbang_self')}
                    className="w-full px-3 py-2 bg-yellow-300 hover:bg-yellow-400 rounded text-sm font-semibold transition-colors text-black"
                >
                    💡 Flashbang (Self Test)
                </button>
            </div>
        </div>
    )
}
