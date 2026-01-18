import { useEffect, useState } from 'react'
import { useGameStore } from '../store/gameStore'
import { PlayerHealthBar } from './PlayerHealthBar'
import { ProblemCard } from './ProblemCard'
import { CodeEditor } from './CodeEditor'
import { TestFeedback } from './TestFeedback'
import { PlayerSelectionModal } from './PlayerSelectionModal'
import { DebugMenu } from './DebugMenu'

interface GameScreenProps {
  emitSelectCard: (cardId: string) => void
  emitSubmitSolution: (cardId: string, code: string) => void
  emitPlayerEliminated: () => void
  socket: any // Socket instance for listening to events
}

export function GameScreen({ emitSelectCard, emitSubmitSolution, emitPlayerEliminated, socket }: GameScreenProps) {
  const {
    players,
    currentPlayerId,
    selectedCardId,
    selectCard,
    updatePlayer,
    gameStatus
  } = useGameStore()

  const [testFeedback, setTestFeedback] = useState<{
    type: 'success' | 'error' | null
    message: string
  }>({ type: null, message: '' })

  // Celebration state for successful card completion
  const [celebration, setCelebration] = useState<{
    show: boolean
    reward: string
  }>({ show: false, reward: '' })

  // Player selection state for targeted debuffs
  const [targetSelection, setTargetSelection] = useState<{
    show: boolean
    targets: Array<{ playerId: string, username: string, timeRemaining: number }>
    rewardValue: number
  }>({ show: false, targets: [], rewardValue: 0 })

  // Animation state for wave effect
  const [hasAnimated, setHasAnimated] = useState(false)

  // Track new card for deal animation
  const [newCardId, setNewCardId] = useState<string | null>(null)

  // Flashbang state
  const [flashbanged, setFlashbanged] = useState(false)

  // Debug menu state
  const [showDebugMenu, setShowDebugMenu] = useState(false)


  // Ticker to force re-renders for timer display
  const [, setTicker] = useState(0)

  // Store final times when game ends
  const [finalTimes, setFinalTimes] = useState<Record<string, number>>({})

  const currentPlayer = currentPlayerId ? players[currentPlayerId] : null
  const selectedCard = currentPlayer?.cards.find(c => c.id === selectedCardId) || null

  // Trigger animation when cards are first loaded
  useEffect(() => {
    if (currentPlayer?.cards && currentPlayer.cards.length > 0 && !hasAnimated) {
      // Small delay to ensure DOM is ready
      setTimeout(() => setHasAnimated(true), 100)
    }
  }, [currentPlayer?.cards, hasAnimated])

  // Listen for solution results
  useEffect(() => {
    if (!socket) return

    const handleSolutionPassed = (data: any) => {
      if (data.playerId === currentPlayerId) {
        // Find the card to get the reward info
        const completedCard = currentPlayer?.cards.find(c => c.id === data.cardId)
        const rewardText = completedCard?.reward
          ? `${completedCard.reward.effect.replace('_', ' ')} ${completedCard.reward.value}s`
          : 'No reward'

        // Show celebration overlay
        setCelebration({ show: true, reward: rewardText })

        // Trigger deal animation for new card
        if (data.newCard?.id) {
          setNewCardId(data.newCard.id)
          // Clear deal animation after it completes
          setTimeout(() => {
            setNewCardId(null)
          }, 800) // deal animation duration
        }

        // Auto-dismiss celebration after 2 seconds
        setTimeout(() => {
          setCelebration({ show: false, reward: '' })
        }, 2000)

        setTestFeedback({
          type: 'success',
          message: 'Great job! All tests passed. Card completed.'
        })
      }
    }

    const handleSolutionFailed = (data: any) => {
      if (data.playerId === currentPlayerId) {
        setTestFeedback({
          type: 'error',
          message: data.error || 'Test failed. Check your code and try again.'
        })
      }
    }

    const handleTargetSelectionRequired = (data: any) => {
      // Show player selection modal after celebration
      setTimeout(() => {
        setTargetSelection({
          show: true,
          targets: data.availableTargets,
          rewardValue: data.value
        })
      }, 2100) // Show after celebration (2s) + small buffer
    }

    const handleFlashbang = () => {
      // Trigger flashbang effect
      setFlashbanged(true)
      // Auto-dismiss after 2 seconds
      setTimeout(() => {
        setFlashbanged(false)
      }, 2000)
    }

    socket.on('solution_passed', handleSolutionPassed)
    socket.on('solution_failed', handleSolutionFailed)
    socket.on('target_selection_required', handleTargetSelectionRequired)
    socket.on('flashbang_applied', handleFlashbang)

    return () => {
      socket.off('solution_passed', handleSolutionPassed)
      socket.off('solution_failed', handleSolutionFailed)
      socket.off('target_selection_required', handleTargetSelectionRequired)
      socket.off('flashbang_applied', handleFlashbang)
    }
  }, [socket, currentPlayerId, currentPlayer])

  // Timer check - runs every 100ms for smooth updates
  useEffect(() => {
    // Stop timer updates when game ends
    if (gameStatus === 'ended') return
    if (!currentPlayer || currentPlayer.isEliminated || !currentPlayer.timerEndTime) return

    const interval = setInterval(() => {
      // Force re-render to update timer display
      setTicker(prev => prev + 1)

      const timeLeft = Math.max(0, Math.floor((currentPlayer.timerEndTime! - Date.now()) / 1000))

      if (timeLeft === 0 && !currentPlayer.isEliminated) {
        // Timer expired - emit player eliminated
        emitPlayerEliminated()
        updatePlayer(currentPlayerId!, { isEliminated: true, eliminatedAt: Date.now(), timerEndTime: null })
      }
    }, 100) // Check every 100ms for smooth countdown

    return () => clearInterval(interval)
  }, [currentPlayerId, currentPlayer, emitPlayerEliminated, updatePlayer, gameStatus])

  const handleCardSelect = (cardId: string) => {
    if (currentPlayer && !currentPlayer.isEliminated) {
      selectCard(cardId)
      // Emit to backend
      emitSelectCard(cardId)
    }
  }

  const handleSubmitSolution = (code: string) => {
    if (!selectedCardId || !currentPlayerId) return

    // Clear any previous feedback
    setTestFeedback({ type: null, message: '' })

    // Emit to backend - backend handles code execution, card removal, and new card addition
    emitSubmitSolution(selectedCardId, code)
  }

  const handleTargetSelect = (targetId: string) => {
    // Emit socket event with selected target
    socket.emit('apply_targeted_debuff', { targetPlayerId: targetId })

    // Close modal
    setTargetSelection({ show: false, targets: [], rewardValue: 0 })
  }

  const handleDebugReward = (rewardType: string) => {
    if (!socket || !currentPlayerId) return

    // Handle flashbang_self separately for testing
    if (rewardType === 'flashbang_self') {
      setFlashbanged(true)
      setTimeout(() => setFlashbanged(false), 2000)
      return
    }

    // Create a mock reward object
    const mockRewards: Record<string, any> = {
      'add_time': { type: 'buff', target: 'self', effect: 'add_time', value: 30 },
      'remove_time': { type: 'debuff', target: 'other', effect: 'remove_time', value: 20 },
      'remove_time_targeted': { type: 'debuff', target: 'targeted', effect: 'remove_time_targeted', value: 50 },
      'remove_time_all': { type: 'debuff', target: 'all', effect: 'remove_time_all', value: 30 },
      'flashbang_targeted': { type: 'debuff', target: 'targeted', effect: 'flashbang_targeted', value: 1 }
    }

    const reward = mockRewards[rewardType]
    if (!reward) return

    // Simulate solution_passed event to trigger reward
    socket.emit('debug_trigger_reward', {
      playerId: currentPlayerId,
      reward: reward
    })
  }

  // Listen for solution failed event (handled by useSocket, but we can show error here)
  // Error handling is done in useSocket hook, but we could add a listener here if needed

  if (!currentPlayer) {
    return <div className="min-h-screen bg-gray-900 text-white p-8">Loading...</div>
  }

  // When a card is selected, hide other cards
  const cardsToShow = selectedCardId ? currentPlayer.cards.filter(c => c.id === selectedCardId) : currentPlayer.cards

  // Capture final times when game ends
  useEffect(() => {
    if (gameStatus === 'ended' && Object.keys(finalTimes).length === 0) {
      const times: Record<string, number> = {}
      Object.values(players).forEach(player => {
        if (player.timerEndTime && !player.isEliminated) {
          times[player.id] = Math.max(0, Math.floor((player.timerEndTime - Date.now()) / 1000))
        } else {
          times[player.id] = 0
        }
      })
      setFinalTimes(times)
    }
  }, [gameStatus, players, finalTimes])

  // Show winner screen if game ended
  if (gameStatus === 'ended') {
    // Rank players: non-eliminated first (by time remaining), then eliminated (by elimination order)
    const rankedPlayers = Object.values(players).sort((a, b) => {
      // Non-eliminated players always rank higher than eliminated players
      if (!a.isEliminated && b.isEliminated) return -1
      if (a.isEliminated && !b.isEliminated) return 1

      // Both non-eliminated: sort by time remaining (more time = higher rank)
      if (!a.isEliminated && !b.isEliminated) {
        return (b.timerEndTime || 0) - (a.timerEndTime || 0)
      }

      // Both eliminated: sort by elimination time (eliminated later = higher rank)
      // Player eliminated last should be 2nd place
      return (b.eliminatedAt || 0) - (a.eliminatedAt || 0)
    })

    const currentPlayerRank = rankedPlayers.findIndex(p => p.id === currentPlayerId) + 1

    return (
      <div className="min-h-screen bg-gray-900 text-white flex items-center justify-center p-8">
        <div className="max-w-2xl w-full">
          <div className="text-center mb-8">
            <h1 className="text-6xl font-bold mb-4">Game Over!</h1>
            {currentPlayerRank === 1 && <p className="text-3xl text-yellow-400 mb-2">🎉 You Won! 🎉</p>}
            <p className="text-xl text-gray-400">
              You placed #{currentPlayerRank} out of {rankedPlayers.length}
            </p>
          </div>

          <div className="bg-gray-800 rounded-xl p-6 shadow-2xl">
            <h2 className="text-2xl font-bold mb-4 text-center">Final Rankings</h2>
            <div className="space-y-3">
              {rankedPlayers.map((player, index) => {
                const isCurrentPlayer = player.id === currentPlayerId
                // Use captured final time instead of calculating dynamically
                const timeRemaining = finalTimes[player.id] || 0
                const minutes = Math.floor(timeRemaining / 60)
                const seconds = timeRemaining % 60

                return (
                  <div
                    key={player.id}
                    className={`flex items-center justify-between p-4 rounded-lg ${isCurrentPlayer ? 'bg-blue-600 border-2 border-blue-400' : 'bg-gray-700'
                      }`}
                  >
                    <div className="flex items-center gap-4">
                      <div className={`text-2xl font-bold w-8 ${index === 0 ? 'text-yellow-400' :
                        index === 1 ? 'text-gray-300' :
                          index === 2 ? 'text-orange-400' :
                            'text-gray-500'
                        }`}>
                        {index === 0 ? '🥇' : index === 1 ? '🥈' : index === 2 ? '🥉' : `#${index + 1}`}
                      </div>
                      <div>
                        <p className="font-semibold text-lg">{player.username}</p>
                        {player.isEliminated && <p className="text-sm text-red-400">Eliminated</p>}
                      </div>
                    </div>
                    <div className="text-right">
                      {!player.isEliminated ? (
                        <p className="text-xl font-mono text-green-400">
                          {minutes}:{String(seconds).padStart(2, '0')}
                        </p>
                      ) : (
                        <p className="text-gray-500">0:00</p>
                      )}
                    </div>
                  </div>
                )
              })}
            </div>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-900 text-white flex">
      {/* Celebration Overlay */}
      {celebration.show && (
        <div className="fixed inset-0 flex items-center justify-center z-50 pointer-events-none">
          <div className="bg-gradient-to-br from-green-400 to-emerald-500 text-white px-12 py-8 rounded-2xl shadow-2xl transform scale-100 animate-bounce">
            <div className="text-center">
              <div className="text-6xl mb-4">🎉</div>
              <h2 className="text-3xl font-bold mb-2">All Tests Passed!</h2>
              <div className="text-xl font-semibold">
                <span className="bg-white/20 px-4 py-2 rounded-lg inline-block">
                  Reward: {celebration.reward}
                </span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Flashbang Overlay */}
      {flashbanged && (
        <div className="fixed inset-0 bg-white z-[70] animate-flashbang pointer-events-none" />
      )}

      {/* Debug Menu Toggle */}
      <button
        onClick={() => setShowDebugMenu(!showDebugMenu)}
        className="fixed bottom-4 right-4 z-50 bg-gray-800 p-2 rounded-full border border-gray-700 hover:bg-gray-700 transition-colors shadow-lg"
        title="Toggle Debug Menu"
      >
        🐛
      </button>

      {/* Debug Menu */}
      {showDebugMenu && (
        <DebugMenu
          onTriggerReward={handleDebugReward}
          onClose={() => setShowDebugMenu(false)}
        />
      )}

      {/* Player Selection Modal */}
      {targetSelection.show && (
        <PlayerSelectionModal
          targets={targetSelection.targets}
          rewardValue={targetSelection.rewardValue}
          onSelect={handleTargetSelect}
        />
      )}



      {/* Left Sidebar - Player Health Bars */}
      <div className="w-80 bg-gray-800 border-r border-gray-700 p-4 overflow-y-auto">
        <h2 className="text-xl font-semibold mb-4">Players</h2>
        {Object.values(players).map((player) => (
          <PlayerHealthBar
            key={player.id}
            player={player}
            isCurrentPlayer={player.id === currentPlayerId}
          />
        ))}
      </div>

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col p-6">

        {/* Selected Problem Card Display */}
        {selectedCard ? (
          <div className="mb-6 bg-gray-800 rounded-lg p-6">
            <div className="flex items-start justify-between mb-4">
              <div>
                <h2 className="text-2xl font-bold mb-2">{selectedCard.problem.title}</h2>
                <span className={`inline-block px-3 py-1 rounded text-sm font-medium ${selectedCard.problem.difficulty === 'Easy' ? 'bg-green-600' :
                  selectedCard.problem.difficulty === 'Medium' ? 'bg-yellow-600' : 'bg-red-600'
                  }`}>
                  {selectedCard.problem.difficulty}
                </span>
              </div>
            </div>

            <p className="text-gray-300 mb-4">{selectedCard.problem.description}</p>

            {/* Function Signature */}
            {selectedCard.problem.functionSignature && (
              <div className="mb-4 p-3 bg-gray-900 rounded-lg">
                <p className="text-sm text-gray-400 mb-1">Function Signature:</p>
                <code className="text-green-400 font-mono">{selectedCard.problem.functionSignature}</code>
              </div>
            )}

            {selectedCard.reward && (
              <div className="mb-2">
                <span className="text-sm px-3 py-1 bg-purple-600/30 text-purple-300 rounded">
                  Reward: {selectedCard.reward.effect.replace('_', ' ')} {selectedCard.reward.value}s
                </span>
              </div>
            )}

            {selectedCard.challenge && (
              <div>
                <span className="text-sm px-3 py-1 bg-orange-600/30 text-orange-300 rounded">
                  Challenge: {selectedCard.challenge.type.replace('_', ' ')} {selectedCard.challenge.value}
                </span>
              </div>
            )}

            <button
              onClick={() => {
                selectCard(null)
                emitSelectCard('') // Clear selection on backend
              }}
              className="mt-4 text-sm text-gray-400 hover:text-white"
            >
              ← Back to cards
            </button>
          </div>
        ) : (
          <div className="flex-1 flex flex-col items-center justify-center">
            <h2 className="text-xl font-semibold mb-8">Select a Problem</h2>
            <div className="flex gap-4 justify-center items-end">
              {cardsToShow.map((card, index) => {
                // Calculate the offset from center for each card
                const totalCards = cardsToShow.length
                const centerIndex = (totalCards - 1) / 2
                const offsetFromCenter = index - centerIndex

                return (
                  <div
                    key={card.id}
                    className="transition-all duration-700 ease-out"
                    style={{
                      transform: hasAnimated
                        ? 'translate(0, 0) rotate(0deg)'
                        : `translate(${-offsetFromCenter * 200}px, 500px) rotate(0deg)`,
                      transitionDelay: hasAnimated ? `${index * 150}ms` : '0ms'
                    }}
                  >
                    <ProblemCard
                      card={card}
                      isSelected={card.id === selectedCardId}
                      onSelect={() => handleCardSelect(card.id)}
                      index={index}
                      isBurning={false}
                      isNewCard={card.id === newCardId}
                    />
                  </div>
                )
              })}
            </div>
          </div>
        )}

        {/* Code Editor */}
        {selectedCard && (
          <div className="flex-1">
            <CodeEditor
              onSubmit={handleSubmitSolution}
              disabled={currentPlayer.isEliminated}
            />
            <TestFeedback
              type={testFeedback.type}
              message={testFeedback.message}
              onDismiss={() => setTestFeedback({ type: null, message: '' })}
            />
          </div>
        )}
      </div>
    </div>
  )
}
