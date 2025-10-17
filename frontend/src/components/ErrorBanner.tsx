import { useAppStore } from '@/store/useAppStore'
import { AlertCircle, CheckCircle2, X } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { useEffect } from 'react'

export function ErrorBanner() {
  const lastError = useAppStore((state) => state.lastError)
  const lastSuccess = useAppStore((state) => state.lastSuccess)
  const setLastError = useAppStore((state) => state.setLastError)
  const setLastSuccess = useAppStore((state) => state.setLastSuccess)

  // Auto-dismiss success after 5s
  useEffect(() => {
    if (lastSuccess) {
      const timer = setTimeout(() => {
        setLastSuccess(null)
      }, 5000)
      return () => clearTimeout(timer)
    }
  }, [lastSuccess, setLastSuccess])

  if (!lastError && !lastSuccess) return null

  return (
    <div className="container mx-auto px-4 py-4">
      {lastError && (
        <div className="flex items-center justify-between rounded-lg border border-destructive bg-destructive/10 px-4 py-3 text-sm">
          <div className="flex items-center gap-2">
            <AlertCircle className="h-5 w-5 text-destructive" />
            <span className="font-medium text-destructive">{lastError}</span>
          </div>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setLastError(null)}
            className="h-auto p-1"
          >
            <X className="h-4 w-4" />
          </Button>
        </div>
      )}

      {lastSuccess && (
        <div className="flex items-center justify-between rounded-lg border border-green-600 bg-green-50 px-4 py-3 text-sm dark:bg-green-950/20">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="h-5 w-5 text-green-600" />
            <span className="font-medium text-green-600 dark:text-green-500">{lastSuccess}</span>
          </div>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setLastSuccess(null)}
            className="h-auto p-1"
          >
            <X className="h-4 w-4" />
          </Button>
        </div>
      )}
    </div>
  )
}

