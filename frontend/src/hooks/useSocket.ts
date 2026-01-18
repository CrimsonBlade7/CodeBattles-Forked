import { useEffect, useState, useCallback } from 'react'
import { io, Socket } from 'socket.io-client'
import { useGameStore, Player, ProblemCard } from '../store/gameStore'

const SOCKET_URL = import.meta.env.VITE_SOCKET_URL || 'http://localhost:5000'

export const useSocket = () => {
  const [socket, setSocket] = useState<Socket | null>(null)
  const [connected, setConnected] = useState(false)

  const {
    setCurrentPlayerId,
    setGameStatus,
    addPlayer,
    updatePlayer,
    removeCard,
    addCard,
    selectCard,
    syncGameState
  } = useGameStore()

  useEffect(() => {
    const newSocket = io(SOCKET_URL, {
      transports: ['polling', 'websocket'], // Try polling first for ngrok stability
    })

    newSocket.on('connect', () => {
      console.log('Connected to server')
      setConnected(true)
    })

    newSocket.on('disconnect', () => {
      console.log('Disconnected from server')
      setConnected(false)
    })

    // Listen for player joined
    newSocket.on('player_joined', (data: { playerId: string; username: string }) => {
      console.log('[Socket] player_joined event received:', data)
      // If this is the current player (we just joined), set currentPlayerId
      const username = useGameStore.getState().username
      console.log('[Socket] Current username in store:', username)
      if (data.username === username) {
        console.log('[Socket] Setting current player ID:', data.playerId)
        setCurrentPlayerId(data.playerId)
      }

      // Add player to store (backend will send full state, but we can add optimistically)
      const newPlayer: Player = {
        id: data.playerId,
        username: data.username,
        timerEndTime: null,  // Will be set when game starts
        isEliminated: false,
        eliminatedAt: null,
        currentProblem: null,
        cards: []
      }
      console.log('[Socket] Adding player to store:', newPlayer)
      addPlayer(newPlayer)
    })

    // Listen for player left
    newSocket.on('player_left', (data: { playerId: string; username: string }) => {
      // Remove player from store
      const currentPlayers = useGameStore.getState().players
      const updatedPlayers = { ...currentPlayers }
      delete updatedPlayers[data.playerId]
      syncGameState({ players: updatedPlayers })
    })

    // Listen for game started
    newSocket.on('game_started', (data: { players: Record<string, Player> }) => {
      setGameStatus('playing')
      // Update all players with their cards
      syncGameState({ players: data.players })
    })

    // Listen for card selected
    newSocket.on('card_selected', (data: { playerId: string; cardId: string; problem: any }) => {
      updatePlayer(data.playerId, { currentProblem: data.cardId })
      // If it's the current player, update selectedCardId
      if (data.playerId === useGameStore.getState().currentPlayerId) {
        selectCard(data.cardId)
      }
    })

    // Listen for solution passed
    newSocket.on('solution_passed', (data: {
      playerId: string
      cardId: string
      testResults: any[]
      newCard: ProblemCard
    }) => {
      console.log('[Socket] Solution passed:', data)
      removeCard(data.playerId, data.cardId)
      addCard(data.playerId, data.newCard)
      // Clear selection if it was the current player
      if (data.playerId === useGameStore.getState().currentPlayerId) {
        selectCard(null)
      }
    })

    // Listen for solution failed
    newSocket.on('solution_failed', (data: {
      playerId: string
      cardId: string
      error: string
      testResults: any[]
    }) => {
      console.error('[Socket] Solution failed:', data)
    })

    // Listen for reward applied
    newSocket.on('reward_applied', (data: {
      playerId?: string
      effect: string
      value: number
      fromPlayer?: string
      affectedPlayers?: Array<{ playerId: string, username: string }>
    }) => {
      // Handle different reward types
      if (data.effect === 'add_time' && data.playerId) {
        const player = useGameStore.getState().players[data.playerId]
        if (player && player.timerEndTime) {
          const newEndTime = player.timerEndTime + (data.value * 1000)
          updatePlayer(data.playerId, { timerEndTime: newEndTime })
        }
      } else if (data.effect === 'remove_time' && data.playerId) {
        const player = useGameStore.getState().players[data.playerId]
        if (player && player.timerEndTime) {
          const newEndTime = Math.max(Date.now(), player.timerEndTime - (data.value * 1000))
          updatePlayer(data.playerId, { timerEndTime: newEndTime })
        }
      } else if (data.effect === 'remove_time_targeted' && data.playerId) {
        const player = useGameStore.getState().players[data.playerId]
        if (player && player.timerEndTime) {
          const newEndTime = Math.max(Date.now(), player.timerEndTime - (data.value * 1000))
          updatePlayer(data.playerId, { timerEndTime: newEndTime })
        }
      } else if (data.effect === 'remove_time_all' && data.affectedPlayers) {
        // Update all affected players
        data.affectedPlayers.forEach(({ playerId }) => {
          const player = useGameStore.getState().players[playerId]
          if (player && player.timerEndTime) {
            const newEndTime = Math.max(Date.now(), player.timerEndTime - (data.value * 1000))
            updatePlayer(playerId, { timerEndTime: newEndTime })
          }
        })
      }
    })

    // Listen for player eliminated
    newSocket.on('player_eliminated', (data: { playerId: string; username: string; eliminatedAt: number }) => {
      updatePlayer(data.playerId, { isEliminated: true, eliminatedAt: data.eliminatedAt, timerEndTime: null })
    })

    // Listen for game ended
    newSocket.on('game_ended', (data: { winner: string | null; winnerName?: string }) => {
      setGameStatus('ended')
      // Could show winner screen here
      console.log('Game ended. Winner:', data.winnerName || 'None')
    })

    // Listen for game state updates
    newSocket.on('game_state', (data: { players: Record<string, Player> }) => {
      console.log('[Socket] game_state event received:', data)
      syncGameState({ players: data.players })
    })

    // Listen for errors
    newSocket.on('error', (data: { message: string }) => {
      console.error('Socket error:', data.message)
    })

    setSocket(newSocket)

    return () => {
      newSocket.close()
    }
  }, [setCurrentPlayerId, setGameStatus, addPlayer, updatePlayer, removeCard, addCard, selectCard, syncGameState])

  const emitJoinRoom = useCallback((username: string, roomCode: string) => {
    console.log('[Socket] emitJoinRoom called with:', { username, roomCode, connected: socket?.connected })
    if (socket?.connected) {
      console.log('[Socket] Emitting join_room event')
      socket.emit('join_room', { username, roomCode })
    } else {
      console.error('[Socket] Cannot emit join_room - socket not connected')
    }
  }, [socket])

  const emitStartGame = useCallback(() => {
    if (socket?.connected) {
      socket.emit('start_game')
    }
  }, [socket])

  const emitSelectCard = useCallback((cardId: string) => {
    if (socket?.connected) {
      const playerId = useGameStore.getState().currentPlayerId
      if (playerId) {
        socket.emit('select_card', { cardId, playerId })
      }
    }
  }, [socket])

  const emitSubmitSolution = useCallback((cardId: string, code: string) => {
    if (socket?.connected) {
      const playerId = useGameStore.getState().currentPlayerId
      if (playerId) {
        socket.emit('submit_solution', { cardId, code, playerId })
      }
    }
  }, [socket])

  const emitPlayerEliminated = useCallback(() => {
    if (socket?.connected) {
      socket.emit('player_eliminated', {})
    }
  }, [socket])

  return {
    socket,
    connected,
    emitJoinRoom,
    emitStartGame,
    emitSelectCard,
    emitSubmitSolution,
    emitPlayerEliminated,
  }
}
