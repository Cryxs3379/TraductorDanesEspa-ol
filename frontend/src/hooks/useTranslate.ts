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
  const maxTokensMode = useAppStore((state) => state.maxTokensMode)
  const maxNewTokens = useAppStore((state) => state.maxNewTokens)
  const strictMax = useAppStore((state) => state.strictMax)
  const glossaryText = useAppStore((state) => state.glossaryText)
  const setIsTranslating = useAppStore((state) => state.setIsTranslating)
  const setLastLatencyMs = useAppStore((state) => state.setLastLatencyMs)
  const setLastError = useAppStore((state) => state.setLastError)
  const setLastSuccess = useAppStore((state) => state.setLastSuccess)

  const translate = async (input: string): Promise<string> => {
    // ⚠️ NO usar .trim() - preservamos la estructura exacta del usuario
    if (!input || input.length === 0) {
      throw new Error('El texto no puede estar vacío')
    }

    setIsLoading(true)
    setIsTranslating(true)
    setLastError(null)
    setLastSuccess(null)
    setLastLatencyMs(null)

    const startTime = performance.now()

    try {
      const glossary = parseGlossary(glossaryText)

      // Aplicar formal solo para ES→DA
      const shouldUseFormal = direction === 'es-da' && formal

      let result

      if (mode === 'text') {
        const payload: any = {
          text: input, // ⚠️ NO tocar - preservar saltos de línea exactos
          direction,
          formal: shouldUseFormal,
          glossary,
          preserve_newlines: true, // ✅ Preservar estructura por defecto
        }
        
        // Solo enviar max_new_tokens si modo=manual y el valor es válido
        if (maxTokensMode === 'manual' && Number.isFinite(maxNewTokens)) {
          payload.max_new_tokens = Math.max(1, Math.floor(maxNewTokens))
          payload.strict_max = strictMax
        }
        
        const response = await translateText(payload, apiUrl)
        result = response.data.translations.join('\n\n')
        setLastLatencyMs(response.latencyMs)
      } else {
        const payload: any = {
          html: input, // ⚠️ NO tocar - preservar HTML exacto
          direction,
          formal: shouldUseFormal,
          glossary,
          preserve_newlines: true, // ✅ Preservar estructura HTML por defecto
        }
        
        // Solo enviar max_new_tokens si modo=manual y el valor es válido
        if (maxTokensMode === 'manual' && Number.isFinite(maxNewTokens)) {
          payload.max_new_tokens = Math.max(1, Math.floor(maxNewTokens))
          payload.strict_max = strictMax
        }
        
        const response = await translateHtml(payload, apiUrl)
        result = response.data.html
        setLastLatencyMs(response.latencyMs)
      }

      const totalTime = Math.round(performance.now() - startTime)
      setLastSuccess(`✓ Traducción completada en ${totalTime}ms`)
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

