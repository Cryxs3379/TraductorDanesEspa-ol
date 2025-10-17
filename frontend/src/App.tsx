import { useEffect } from 'react'
import { useAppStore } from './store/useAppStore'
import { Home } from './pages/Home'
import { TooltipProvider } from './components/ui/tooltip'

function App() {
  const loadFromLocalStorage = useAppStore((state) => state.loadFromLocalStorage)

  useEffect(() => {
    // Cargar configuración guardada al montar
    loadFromLocalStorage()
  }, [loadFromLocalStorage])

  return (
    <TooltipProvider>
      <Home />
    </TooltipProvider>
  )
}

export default App

