import { useState } from 'react'
import { useAppStore } from '@/store/useAppStore'
import { Textarea } from '@/components/ui/textarea'
import { Button } from '@/components/ui/button'
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog'
import { Label } from '@/components/ui/label'
import { BookOpen, Download, Upload } from 'lucide-react'
import { downloadFile } from '@/lib/utils'

export function GlossaryPanel() {
  const glossaryText = useAppStore((state) => state.glossaryText)
  const setGlossaryText = useAppStore((state) => state.setGlossaryText)
  const direction = useAppStore((state) => state.direction)
  const [open, setOpen] = useState(false)

  const handleExport = () => {
    if (!glossaryText.trim()) return
    const filename = `glossary-${direction}-${Date.now()}.txt`
    downloadFile(glossaryText, filename, 'text/plain')
  }

  const handleImport = () => {
    const input = document.createElement('input')
    input.type = 'file'
    input.accept = '.txt'
    input.onchange = (e) => {
      const file = (e.target as HTMLInputElement).files?.[0]
      if (file) {
        const reader = new FileReader()
        reader.onload = (event) => {
          const text = event.target?.result as string
          setGlossaryText(text)
        }
        reader.readAsText(file)
      }
    }
    input.click()
  }

  const placeholder = direction === 'es-da'
    ? 'Ejemplo:\ncomputadora=computer\nsistema operativo=operativsystem'
    : 'Exempel:\ncomputer=computadora\noperativsystem=sistema operativo'

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button variant="outline" size="sm">
          <BookOpen className="mr-2 h-4 w-4" />
          Glosario
          {glossaryText.trim() && (
            <span className="ml-2 rounded-full bg-primary px-2 py-0.5 text-xs text-primary-foreground">
              {glossaryText.trim().split('\n').filter(l => l.trim()).length}
            </span>
          )}
        </Button>
      </DialogTrigger>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle>Editor de Glosario</DialogTitle>
          <DialogDescription>
            Define términos específicos para traducir. Formato: <code>término_origen=término_destino</code> (una línea por término).
          </DialogDescription>
        </DialogHeader>
        <div className="space-y-4">
          <div>
            <Label htmlFor="glossary-text">
              Términos ({direction === 'es-da' ? 'Español → Danés' : 'Danés → Español'})
            </Label>
            <Textarea
              id="glossary-text"
              value={glossaryText}
              onChange={(e) => setGlossaryText(e.target.value)}
              placeholder={placeholder}
              rows={12}
              className="font-mono text-sm"
            />
          </div>
          <div className="flex justify-between">
            <div className="flex gap-2">
              <Button variant="outline" size="sm" onClick={handleImport}>
                <Upload className="mr-2 h-4 w-4" />
                Importar
              </Button>
              <Button variant="outline" size="sm" onClick={handleExport} disabled={!glossaryText.trim()}>
                <Download className="mr-2 h-4 w-4" />
                Exportar
              </Button>
            </div>
            <Button onClick={() => setOpen(false)}>Cerrar</Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  )
}

