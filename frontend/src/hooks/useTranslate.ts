import { useState } from 'react'
import { useAppStore } from '@/store/useAppStore'
import { translateText, translateHtml } from '@/lib/api'
import { parseGlossary } from '@/lib/utils'
import type { TranslationMode, ApiError } from '@/lib/types'

export function useTranslate(mode: TranslationMode) {
  const [isLoading, setIsLoading] = useState(false)

  const apiUrl = useAppStore((state) => state.apiUrl)
  const direction = useAppStore((state) => state.direction)
  const formal = useAppStore((state) => state.formal)
  const maxNewTokens = useAppStore((state) => state.maxNewTokens)
  const glossaryText = useAppStore((state) => state.glossaryText)
  const setIsTranslating = useAppStore((state) => state.setIsTranslating)
  const setLastLatencyMs = useAppStore((state) => state.setLastLatencyMs)
  const setLastError = useAppStore((state) => state.setLastError)
  const setLastSuccess = useAppStore((state) => state.setLastSuccess)

  const translate = async (input: string): Promise<string> => {
    if (!input.trim()) {
      throw new Error('El texto no puede estar vacío')
    }

    setIsLoading(true)
    setIsTranslating(true)
    setLastError(null)
    setLastSuccess(null)
    setLastLatencyMs(null)

    try {
      const glossary = parseGlossary(glossaryText)

      // Aplicar formal solo para ES→DA
      const shouldUseFormal = direction === 'es-da' && formal

      let result

      if (mode === 'text') {
        const response = await translateText(
          {
            text: input,
            direction,
            formal: shouldUseFormal,
            max_new_tokens: maxNewTokens,
            glossary,
          },
          apiUrl
        )
        result = response.data.translations.join('\n\n')
        setLastLatencyMs(response.latencyMs)
      } else {
        const response = await translateHtml(
          {
            html: input,
            direction,
            formal: shouldUseFormal,
            max_new_tokens: maxNewTokens,
            glossary,
          },
          apiUrl
        )
        result = response.data.html
        setLastLatencyMs(response.latencyMs)
      }

      setLastSuccess(`✓ Traducción completada en ${Math.round(performance.now() - performance.now())}ms`)
      return result
    } catch (error) {
      const apiError = error as ApiError
      setLastError(apiError.message || 'Error desconocido durante la traducción')
      throw error
    } finally {
      setIsLoading(false)
      setIsTranslating(false)
    }
  }

  return { translate, isLoading }
}

