import { useState, useEffect } from 'react'
import { useAppStore } from '@/store/useAppStore'
import { Textarea } from '@/components/ui/textarea'
import { Button } from '@/components/ui/button'
import { Label } from '@/components/ui/label'
import { Switch } from '@/components/ui/switch'
import { GlossaryPanel } from './GlossaryPanel'
import { CopyButtons } from './CopyButtons'
import { useTranslate } from '@/hooks/useTranslate'
import { Loader2, Languages } from 'lucide-react'

export function TextTranslator() {
  const [sourceText, setSourceText] = useState('')
  const [targetText, setTargetText] = useState('')

  const direction = useAppStore((state) => state.direction)
  const formal = useAppStore((state) => state.formal)
  const setFormal = useAppStore((state) => state.setFormal)
  const health = useAppStore((state) => state.health)

  const { translate, isLoading } = useTranslate('text')

  const handleTranslate = async () => {
    try {
      const result = await translate(sourceText)
      setTargetText(result)
    } catch (error) {
      console.error('Translation error:', error)
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
      e.preventDefault()
      if (canTranslate) {
        handleTranslate()
      }
    }
  }

  const canTranslate = sourceText.trim().length > 0 && health?.model_loaded && !isLoading

  const getPlaceholder = (type: 'source' | 'target') => {
    if (direction === 'es-da') {
      return type === 'source'
        ? 'Escribe o pega tu texto en español aquí...\n\nAtajo: Ctrl+Enter para traducir'
        : 'La traducción al danés aparecerá aquí'
    } else {
      return type === 'source'
        ? 'Skriv eller indsæt din tekst på dansk her...\n\nGenvej: Ctrl+Enter til oversættelse'
        : 'La traducción al español aparecerá aquí'
    }
  }

  // Limpiar salida cuando cambia la dirección
  useEffect(() => {
    setTargetText('')
  }, [direction])

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      {/* Panel de entrada */}
      <div className="flex flex-col gap-4">
        <div className="flex items-center justify-between">
          <Label htmlFor="source-text" className="text-base font-semibold">
            {direction === 'es-da' ? '🇪🇸 Español' : '🇩🇰 Danés'}
          </Label>
          <div className="flex items-center gap-4">
            {/* Switch formal solo visible para ES→DA */}
            {direction === 'es-da' && (
              <div className="flex items-center gap-2">
                <Switch
                  id="formal-switch"
                  checked={formal}
                  onCheckedChange={setFormal}
                />
                <Label htmlFor="formal-switch" className="text-sm cursor-pointer">
                  Formal (De/Dem)
                </Label>
              </div>
            )}
            <GlossaryPanel />
          </div>
        </div>

        <Textarea
          id="source-text"
          value={sourceText}
          onChange={(e) => setSourceText(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={getPlaceholder('source')}
          rows={15}
          className="flex-1 font-sans"
        />

        <div className="flex items-center justify-between text-sm text-muted-foreground">
          <span>{sourceText.length} caracteres</span>
          {sourceText.length > 10000 && (
            <span className="text-yellow-600">
              Texto largo: puede tardar más tiempo
            </span>
          )}
        </div>

        <Button
          onClick={handleTranslate}
          disabled={!canTranslate}
          size="lg"
          className="w-full"
        >
          {isLoading ? (
            <>
              <Loader2 className="mr-2 h-5 w-5 animate-spin" />
              Traduciendo...
            </>
          ) : (
            <>
              <Languages className="mr-2 h-5 w-5" />
              Traducir (Ctrl+Enter)
            </>
          )}
        </Button>
      </div>

      {/* Panel de salida */}
      <div className="flex flex-col gap-4">
        <div className="flex items-center justify-between">
          <Label htmlFor="target-text" className="text-base font-semibold">
            {direction === 'es-da' ? '🇩🇰 Danés' : '🇪🇸 Español'}
          </Label>
          <CopyButtons content={targetText} />
        </div>

        <Textarea
          id="target-text"
          value={targetText}
          readOnly
          placeholder={getPlaceholder('target')}
          rows={15}
          className="flex-1 font-sans bg-muted/30"
        />

        <div className="text-sm text-muted-foreground">
          {targetText.length} caracteres
        </div>
      </div>
    </div>
  )
}

