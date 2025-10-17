import { useState, useEffect } from 'react'
import { useAppStore } from '@/store/useAppStore'
import { Textarea } from '@/components/ui/textarea'
import { Button } from '@/components/ui/button'
import { Label } from '@/components/ui/label'
import { Switch } from '@/components/ui/switch'
import { GlossaryPanel } from './GlossaryPanel'
import { CopyButtons } from './CopyButtons'
import { useTranslate } from '@/hooks/useTranslate'
import { Loader2, Languages, Eye, Code } from 'lucide-react'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'

export function HtmlTranslator() {
  const [sourceHtml, setSourceHtml] = useState('')
  const [targetHtml, setTargetHtml] = useState('')
  const [outputView, setOutputView] = useState<'code' | 'preview'>('code')

  const direction = useAppStore((state) => state.direction)
  const formal = useAppStore((state) => state.formal)
  const setFormal = useAppStore((state) => state.setFormal)
  const health = useAppStore((state) => state.health)

  const { translate, isLoading } = useTranslate('html')

  const handleTranslate = async () => {
    try {
      const result = await translate(sourceHtml)
      setTargetHtml(result)
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

  const canTranslate = sourceHtml.trim().length > 0 && health?.model_loaded && !isLoading

  const getPlaceholder = () => {
    if (direction === 'es-da') {
      return 'Pega el código HTML de tu correo en español aquí...\n\nEjemplo:\n<p>Hola <strong>mundo</strong></p>\n<ul>\n  <li>Item 1</li>\n  <li>Item 2</li>\n</ul>'
    } else {
      return 'Indsæt HTML-koden fra din e-mail på dansk her...\n\nEksempel:\n<p>Hej <strong>verden</strong></p>\n<ul>\n  <li>Punkt 1</li>\n  <li>Punkt 2</li>\n</ul>'
    }
  }

  // Limpiar salida cuando cambia la dirección
  useEffect(() => {
    setTargetHtml('')
  }, [direction])

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      {/* Panel de entrada */}
      <div className="flex flex-col gap-4">
        <div className="flex items-center justify-between">
          <Label htmlFor="source-html" className="text-base font-semibold">
            HTML {direction === 'es-da' ? '🇪🇸 Español' : '🇩🇰 Danés'}
          </Label>
          <div className="flex items-center gap-4">
            {direction === 'es-da' && (
              <div className="flex items-center gap-2">
                <Switch
                  id="formal-switch-html"
                  checked={formal}
                  onCheckedChange={setFormal}
                />
                <Label htmlFor="formal-switch-html" className="text-sm cursor-pointer">
                  Formal (De/Dem)
                </Label>
              </div>
            )}
            <GlossaryPanel />
          </div>
        </div>

        <Textarea
          id="source-html"
          value={sourceHtml}
          onChange={(e) => setSourceHtml(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={getPlaceholder()}
          rows={15}
          className="flex-1 font-mono text-sm"
        />

        <div className="flex items-center justify-between text-sm text-muted-foreground">
          <span>{sourceHtml.length} caracteres</span>
          {sourceHtml.length > 20000 && (
            <span className="text-yellow-600">
              HTML largo: puede tardar más tiempo
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
              Traduciendo HTML...
            </>
          ) : (
            <>
              <Languages className="mr-2 h-5 w-5" />
              Traducir HTML (Ctrl+Enter)
            </>
          )}
        </Button>
      </div>

      {/* Panel de salida */}
      <div className="flex flex-col gap-4">
        <div className="flex items-center justify-between">
          <Label className="text-base font-semibold">
            HTML {direction === 'es-da' ? '🇩🇰 Danés' : '🇪🇸 Español'}
          </Label>
          <div className="flex items-center gap-2">
            <Tabs value={outputView} onValueChange={(v) => setOutputView(v as 'code' | 'preview')}>
              <TabsList>
                <TabsTrigger value="code" className="text-xs">
                  <Code className="mr-1 h-3 w-3" />
                  Código
                </TabsTrigger>
                <TabsTrigger value="preview" className="text-xs">
                  <Eye className="mr-1 h-3 w-3" />
                  Vista previa
                </TabsTrigger>
              </TabsList>
            </Tabs>
            <CopyButtons content={targetHtml} mimeType="text/html" />
          </div>
        </div>

        {outputView === 'code' ? (
          <Textarea
            value={targetHtml}
            readOnly
            placeholder="El HTML traducido aparecerá aquí"
            rows={15}
            className="flex-1 font-mono text-sm bg-muted/30"
          />
        ) : (
          <div className="flex-1 rounded-md border bg-muted/30 p-4 overflow-auto min-h-[360px]">
            {targetHtml ? (
              <div dangerouslySetInnerHTML={{ __html: targetHtml }} />
            ) : (
              <p className="text-sm text-muted-foreground">
                La vista previa del HTML traducido aparecerá aquí
              </p>
            )}
          </div>
        )}

        <div className="text-sm text-muted-foreground">
          {targetHtml.length} caracteres
        </div>
      </div>
    </div>
  )
}

