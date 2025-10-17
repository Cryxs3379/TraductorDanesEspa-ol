import { useEffect } from 'react'
import { useAppStore } from '@/store/useAppStore'
import { getHealth, getInfo } from '@/lib/api'
import { Button } from '@/components/ui/button'
import { RefreshCw, Activity } from 'lucide-react'
import { formatNumber } from '@/lib/utils'

export function MetricsBar() {
  const apiUrl = useAppStore((state) => state.apiUrl)
  const health = useAppStore((state) => state.health)
  const info = useAppStore((state) => state.info)
  const lastLatencyMs = useAppStore((state) => state.lastLatencyMs)
  const setHealth = useAppStore((state) => state.setHealth)
  const setInfo = useAppStore((state) => state.setInfo)

  const fetchMetrics = async () => {
    try {
      const [healthRes, infoRes] = await Promise.all([
        getHealth(apiUrl),
        getInfo(apiUrl),
      ])
      setHealth(healthRes.data)
      setInfo(infoRes.data)
    } catch (error) {
      console.error('Error fetching metrics:', error)
      setHealth(null)
      setInfo(null)
    }
  }

  useEffect(() => {
    fetchMetrics()
    // Refrescar cada 30s
    const interval = setInterval(fetchMetrics, 30000)
    return () => clearInterval(interval)
  }, [apiUrl])

  const getStatusColor = () => {
    if (!health) return 'bg-red-500'
    if (health.model_loaded) return 'bg-green-500'
    return 'bg-yellow-500'
  }

  const getStatusText = () => {
    if (!health) return 'Offline'
    if (health.model_loaded) return 'Listo'
    return 'Cargando...'
  }

  return (
    <div className="fixed bottom-0 left-0 right-0 border-t bg-card px-4 py-2 text-sm">
      <div className="container mx-auto flex items-center justify-between">
        <div className="flex items-center gap-4">
          {/* Status */}
          <div className="flex items-center gap-2">
            <div className={`h-2 w-2 rounded-full ${getStatusColor()}`} />
            <span className="font-medium">{getStatusText()}</span>
          </div>

          {/* Latencia */}
          {lastLatencyMs !== null && (
            <div className="flex items-center gap-1 text-muted-foreground">
              <Activity className="h-3 w-3" />
              <span>{lastLatencyMs}ms</span>
            </div>
          )}

          {/* Cache */}
          {info?.cache && (
            <div className="flex items-center gap-2 text-muted-foreground">
              <span>
                Cache: {info.cache.hit_rate} ({formatNumber(info.cache.hits)} hits, {formatNumber(info.cache.currsize)} entries)
              </span>
            </div>
          )}

          {/* Uptime */}
          {info?.uptime && (
            <div className="text-muted-foreground">
              Uptime: {info.uptime}
            </div>
          )}
        </div>

        {/* Botón refrescar */}
        <Button variant="ghost" size="sm" onClick={fetchMetrics}>
          <RefreshCw className="h-4 w-4" />
        </Button>
      </div>
    </div>
  )
}

