import { create } from 'zustand'

export interface TestCase {
  input: any
  expectedOutput: any
}

export interface ProblemCard {
  id: string
  problem: {
    title: string
    description: string
    difficulty: 'Easy' | 'Medium' | 'Hard'
    functionSignature: string
    testCases: TestCase[]
  }
  reward?: {
    type: 'buff' | 'debuff'
    target: 'self' | 'other'
    effect: 'freeze_time' | 'add_time' | 'remove_time'
    value: number
  }
  challenge?: {
    type: 'time_limit' | 'line_limit' | 'complexity'
    value: number | string
  }
}

export interface Player {
  id: string
  username: string
  timerEndTime: number | null  // Unix timestamp in milliseconds when timer expires
  isEliminated: boolean
  eliminatedAt: number | null  // Unix timestamp in milliseconds when player was eliminated
  currentProblem: string | null
  cards: ProblemCard[]
}

interface GameState {
  // Current player info
  currentPlayerId: string | null
  username: string
  roomCode: string

  // All players
  players: Record<string, Player>

  // Game status
  gameStatus: 'menu' | 'lobby' | 'playing' | 'ended'
  selectedCardId: string | null

  // Actions
  setUsername: (username: string) => void
  joinRoom: (roomCode: string) => void
  setGameStatus: (status: 'menu' | 'lobby' | 'playing' | 'ended') => void
  addPlayer: (player: Player) => void
  updatePlayer: (playerId: string, updates: Partial<Player>) => void
  selectCard: (cardId: string | null) => void
  removeCard: (playerId: string, cardId: string) => void
  addCard: (playerId: string, card: ProblemCard) => void
  startGame: () => void
  syncGameState: (gameState: { players: Record<string, Player>, gameStatus?: 'menu' | 'lobby' | 'playing' | 'ended', currentPlayerId?: string }) => void
  setCurrentPlayerId: (playerId: string) => void
}


export const useGameStore = create<GameState>((set, get) => ({
  currentPlayerId: null,
  username: '',
  roomCode: '',
  players: {},
  gameStatus: 'menu',
  selectedCardId: null,

  setUsername: (username) => set({ username }),

  joinRoom: (roomCode) => {
    // Just update room code and status - backend creates player via socket
    set({
      roomCode,
      gameStatus: 'lobby'
    })
  },

  setGameStatus: (status) => set({ gameStatus: status }),

  addPlayer: (player) => set((state) => ({
    players: { ...state.players, [player.id]: player }
  })),

  updatePlayer: (playerId, updates) => set((state) => ({
    players: {
      ...state.players,
      [playerId]: {
        ...state.players[playerId],
        ...updates
      }
    }
  })),

  selectCard: (cardId) => {
    const state = get()
    const playerId = state.currentPlayerId
    if (!playerId) return

    if (cardId === null) {
      set({
        selectedCardId: null,
      })
      get().updatePlayer(playerId, { currentProblem: null })
      return
    }

    const player = state.players[playerId]
    const card = player.cards.find(c => c.id === cardId)

    if (card) {
      set({
        selectedCardId: cardId,
      })
      // Update player's current problem
      get().updatePlayer(playerId, { currentProblem: cardId })
    }
  },

  removeCard: (playerId, cardId) => set((state) => {
    const player = state.players[playerId]
    if (!player) return state

    return {
      players: {
        ...state.players,
        [playerId]: {
          ...player,
          cards: player.cards.filter(c => c.id !== cardId),
          currentProblem: player.currentProblem === cardId ? null : player.currentProblem
        }
      },
      selectedCardId: state.selectedCardId === cardId ? null : state.selectedCardId
    }
  }),

  addCard: (playerId, card) => set((state) => {
    const player = state.players[playerId]
    if (!player) return state

    return {
      players: {
        ...state.players,
        [playerId]: {
          ...player,
          cards: [...player.cards, card]
        }
      }
    }
  }),

  startGame: () => {
    // Just update status - backend deals cards via game_started event
    set({ gameStatus: 'playing' })
  },

  syncGameState: (gameState: { players: Record<string, Player>, gameStatus?: 'menu' | 'lobby' | 'playing' | 'ended', currentPlayerId?: string }) => {
    set({
      players: gameState.players,
      gameStatus: gameState.gameStatus || get().gameStatus,
      currentPlayerId: gameState.currentPlayerId || get().currentPlayerId
    })
  },

  setCurrentPlayerId: (playerId: string) => {
    set({ currentPlayerId: playerId })
  }
}))