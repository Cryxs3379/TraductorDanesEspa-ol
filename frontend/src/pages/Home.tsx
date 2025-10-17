import { useAppStore } from '@/store/useAppStore'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { DirectionSelect } from '@/components/DirectionSelect'
import { ApiUrlInput } from '@/components/ApiUrlInput'
import { TextTranslator } from '@/components/TextTranslator'
import { HtmlTranslator } from '@/components/HtmlTranslator'
import { ErrorBanner } from '@/components/ErrorBanner'
import { MetricsBar } from '@/components/MetricsBar'
import { FileText, Code2 } from 'lucide-react'

export function Home() {
  const activeTab = useAppStore((state) => state.activeTab)
  const setActiveTab = useAppStore((state) => state.setActiveTab)

  return (
    <div className="min-h-screen bg-background pb-16">
      {/* Header */}
      <header className="border-b bg-card">
        <div className="container mx-auto px-4 py-6">
          <div className="flex flex-col gap-6 lg:flex-row lg:items-center lg:justify-between">
            <div className="flex items-center gap-3">
              <h1 className="text-3xl font-bold tracking-tight">
                📧 Traductor <span className="text-primary">ES ↔ DA</span>
              </h1>
              <span className="inline-flex items-center rounded-full bg-green-50 px-3 py-1 text-xs font-medium text-green-700 ring-1 ring-inset ring-green-600/20 dark:bg-green-950 dark:text-green-400">
                🔒 Offline
              </span>
            </div>

            <div className="flex flex-col gap-4 lg:flex-row lg:items-center">
              <DirectionSelect />
              <div className="lg:max-w-xs">
                <ApiUrlInput />
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Error/Success Banner */}
      <ErrorBanner />

      {/* Main Content */}
      <main className="container mx-auto px-4 py-8">
        <Tabs value={activeTab} onValueChange={(v) => setActiveTab(v as 'text' | 'html')}>
          <TabsList className="mb-6">
            <TabsTrigger value="text" className="flex items-center gap-2">
              <FileText className="h-4 w-4" />
              Texto
            </TabsTrigger>
            <TabsTrigger value="html" className="flex items-center gap-2">
              <Code2 className="h-4 w-4" />
              Correo (HTML)
            </TabsTrigger>
          </TabsList>

          <TabsContent value="text">
            <TextTranslator />
          </TabsContent>

          <TabsContent value="html">
            <HtmlTranslator />
          </TabsContent>
        </Tabs>
      </main>

      {/* Metrics Bar */}
      <MetricsBar />
    </div>
  )
}

