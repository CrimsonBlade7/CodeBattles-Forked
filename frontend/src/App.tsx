import { useGameStore } from './store/gameStore'
import { useSocket } from './hooks/useSocket'
import { StartMenu } from './components/StartMenu'
import { Lobby } from './components/Lobby'
import { GameScreen } from './components/GameScreen'

function App() {
  const gameStatus = useGameStore((state) => state.gameStatus)
  const socketProps = useSocket()

  if (gameStatus === 'menu') {
    return <StartMenu {...socketProps} />
  }

  if (gameStatus === 'lobby') {
    return <Lobby {...socketProps} />
  }

  if (gameStatus === 'playing' || gameStatus === 'ended') {
    return <GameScreen {...socketProps} />
  }

  return <StartMenu {...socketProps} />
}

export default App