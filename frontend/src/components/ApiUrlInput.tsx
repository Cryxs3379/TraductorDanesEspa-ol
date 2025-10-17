import { useState } from 'react'
import { useAppStore } from '@/store/useAppStore'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { Label } from '@/components/ui/label'
import { getHealth } from '@/lib/api'
import { Loader2, CheckCircle2, AlertCircle } from 'lucide-react'

export function ApiUrlInput() {
  const apiUrl = useAppStore((state) => state.apiUrl)
  const setApiUrl = useAppStore((state) => state.setApiUrl)
  const [localUrl, setLocalUrl] = useState(apiUrl)
  const [testing, setTesting] = useState(false)
  const [testResult, setTestResult] = useState<'success' | 'error' | null>(null)

  const handleTest = async () => {
    setTesting(true)
    setTestResult(null)
    try {
      await getHealth(localUrl)
      setTestResult('success')
      setApiUrl(localUrl)
    } catch {
      setTestResult('error')
    } finally {
      setTesting(false)
    }
  }

  const handleBlur = () => {
    if (localUrl !== apiUrl && !testing) {
      setApiUrl(localUrl)
    }
  }

  return (
    <div className="flex flex-col gap-2">
      <Label htmlFor="api-url" className="text-sm font-medium">
        URL del backend:
      </Label>
      <div className="flex gap-2">
        <Input
          id="api-url"
          type="url"
          value={localUrl}
          onChange={(e) => setLocalUrl(e.target.value)}
          onBlur={handleBlur}
          placeholder="http://localhost:8000"
          className="flex-1"
        />
        <Button onClick={handleTest} disabled={testing} variant="outline" size="sm">
          {testing && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
          {!testing && testResult === 'success' && (
            <CheckCircle2 className="mr-2 h-4 w-4 text-green-600" />
          )}
          {!testing && testResult === 'error' && (
            <AlertCircle className="mr-2 h-4 w-4 text-red-600" />
          )}
          Probar
        </Button>
      </div>
      {testResult === 'error' && (
        <p className="text-xs text-destructive">No se pudo conectar al backend</p>
      )}
    </div>
  )
}

