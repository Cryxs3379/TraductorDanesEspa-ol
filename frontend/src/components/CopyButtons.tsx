import { Button } from '@/components/ui/button'
import { Copy, Download, Check } from 'lucide-react'
import { downloadFile } from '@/lib/utils'
import { useState } from 'react'
import { useAppStore } from '@/store/useAppStore'

interface CopyButtonsProps {
  content: string
  filename?: string
  mimeType?: string
}

export function CopyButtons({ content, filename, mimeType = 'text/plain' }: CopyButtonsProps) {
  const [copied, setCopied] = useState(false)
  const direction = useAppStore((state) => state.direction)
  const activeTab = useAppStore((state) => state.activeTab)

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(content)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch (error) {
      console.error('Error copying to clipboard:', error)
    }
  }

  const handleDownload = () => {
    const defaultFilename = filename || `traduccion-${direction}-${Date.now()}.${activeTab === 'html' ? 'html' : 'txt'}`
    downloadFile(content, defaultFilename, mimeType)
  }

  return (
    <div className="flex gap-2">
      <Button
        variant="outline"
        size="sm"
        onClick={handleCopy}
        disabled={!content || copied}
      >
        {copied ? (
          <>
            <Check className="mr-2 h-4 w-4" />
            Copiado
          </>
        ) : (
          <>
            <Copy className="mr-2 h-4 w-4" />
            Copiar
          </>
        )}
      </Button>
      <Button
        variant="outline"
        size="sm"
        onClick={handleDownload}
        disabled={!content}
      >
        <Download className="mr-2 h-4 w-4" />
        Guardar
      </Button>
    </div>
  )
}

