import { useState, useEffect } from 'react'
import { useGameStore } from '../store/gameStore'

interface StartMenuProps {
    emitJoinRoom: (username: string, roomCode: string) => void
    connected: boolean
}

export function StartMenu({ emitJoinRoom, connected }: StartMenuProps) {
    const [username, setUsername] = useState('')
    const [roomCode, setRoomCode] = useState('')
    const [mode, setMode] = useState<'select' | 'host' | 'join'>('select') // select, host, or join
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

            // Empty string = create new room, otherwise join existing
            const finalRoomCode = mode === 'host' ? '' : roomCode.trim().toUpperCase()

            joinRoom(finalRoomCode || 'LOADING') // Temporary, will be updated by backend
            // Emit join_room event to backend
            emitJoinRoom(username.trim(), finalRoomCode)
        }
    }

    const handleBack = () => {
        setMode('select')
        setRoomCode('')
    }

    // Mode selection screen
    if (mode === 'select') {
        return (
            <div className="min-h-screen bg-gray-900 text-white flex items-center justify-center">
                <div className="max-w-md w-full p-8">
                    <div className="text-center mb-8">
                        <h1 className="text-5xl font-bold mb-2 bg-gradient-to-r from-blue-400 to-purple-600 bg-clip-text text-transparent">
                            CodeBattles
                        </h1>
                        <p className="text-gray-400">Speed Coding Party Game</p>
                    </div>

                    <div className="bg-gray-800 rounded-lg p-6 space-y-4">
                        <button
                            onClick={() => setMode('host')}
                            disabled={!connected}
                            className="w-full py-4 bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 rounded-lg font-semibold text-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                            🎮 Host New Game
                        </button>

                        <button
                            onClick={() => setMode('join')}
                            disabled={!connected}
                            className="w-full py-4 bg-gray-700 hover:bg-gray-600 rounded-lg font-semibold text-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                            🚪 Join Existing Game
                        </button>

                        {!connected && (
                            <div className="text-red-400 text-sm text-center mt-4">
                                Connecting to server...
                            </div>
                        )}
                    </div>
                </div>
            </div>
        )
    }

    // Host or Join form
    return (
        <div className="min-h-screen bg-gray-900 text-white flex items-center justify-center">
            <div className="max-w-md w-full p-8">
                <div className="text-center mb-8">
                    <h1 className="text-5xl font-bold mb-2 bg-gradient-to-r from-blue-400 to-purple-600 bg-clip-text text-transparent">
                        CodeBattles
                    </h1>
                    <p className="text-gray-400">
                        {mode === 'host' ? 'Host New Game' : 'Join Existing Game'}
                    </p>
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
                            autoFocus
                            disabled={!connected}
                            className="w-full px-4 py-3 bg-gray-700 border border-gray-600 rounded-lg focus:outline-none focus:border-blue-500 text-white disabled:opacity-50"
                        />
                    </div>

                    {mode === 'join' && (
                        <div>
                            <label htmlFor="roomCode" className="block text-sm font-medium mb-2">
                                Room Code
                            </label>
                            <input
                                id="roomCode"
                                type="text"
                                value={roomCode}
                                onChange={(e) => setRoomCode(e.target.value.toUpperCase())}
                                placeholder="Enter 6-character code"
                                maxLength={6}
                                required
                                disabled={!connected}
                                className="w-full px-4 py-3 bg-gray-700 border border-gray-600 rounded-lg focus:outline-none focus:border-blue-500 text-white font-mono text-center text-2xl tracking-widest disabled:opacity-50"
                            />
                        </div>
                    )}

                    {!connected && (
                        <div className="text-red-400 text-sm text-center">
                            Connecting to server...
                        </div>
                    )}

                    <div className="flex gap-3">
                        <button
                            type="button"
                            onClick={handleBack}
                            className="flex-1 py-3 bg-gray-700 hover:bg-gray-600 rounded-lg font-semibold transition-colors"
                        >
                            ← Back
                        </button>
                        <button
                            type="submit"
                            disabled={!connected || !username.trim() || (mode === 'join' && !roomCode.trim())}
                            className="flex-1 py-3 bg-blue-600 hover:bg-blue-700 rounded-lg font-semibold transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                            {mode === 'host' ? 'Create Room' : 'Join Room'}
                        </button>
                    </div>
                </form>
            </div>
        </div>
    )
}
