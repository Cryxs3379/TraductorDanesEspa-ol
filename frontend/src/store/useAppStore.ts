import { create } from 'zustand'
import type { Direction, TranslationMode, HealthResponse, InfoResponse } from '@/lib/types'

interface AppState {
  // Configuración
  apiUrl: string
  direction: Direction
  formal: boolean
  maxNewTokens: number  // 32-512, default 256
  glossaryText: string

  // UI
  activeTab: TranslationMode
  isTranslating: boolean

  // Resultados
  lastLatencyMs: number | null
  lastError: string | null
  lastSuccess: string | null

  // Métricas del backend
  health: HealthResponse | null
  info: InfoResponse | null

  // Acciones
  setApiUrl: (url: string) => void
  setDirection: (direction: Direction) => void
  setFormal: (formal: boolean) => void
  setMaxNewTokens: (tokens: number) => void
  setGlossaryText: (text: string) => void
  setActiveTab: (tab: TranslationMode) => void
  setIsTranslating: (isTranslating: boolean) => void
  setLastLatencyMs: (latency: number | null) => void
  setLastError: (error: string | null) => void
  setLastSuccess: (message: string | null) => void
  setHealth: (health: HealthResponse | null) => void
  setInfo: (info: InfoResponse | null) => void

  // Persistencia
  loadFromLocalStorage: () => void
  persistToLocalStorage: () => void
}

const STORAGE_KEY = 'traductor-es-da-config'

// Estado inicial
const defaultState = {
  apiUrl: 'http://localhost:8000',
  direction: 'es-da' as Direction,
  formal: false,
  maxNewTokens: 256,  // actualizado de 192 para textos largos
  glossaryText: '',
  activeTab: 'text' as TranslationMode,
  isTranslating: false,
  lastLatencyMs: null,
  lastError: null,
  lastSuccess: null,
  health: null,
  info: null,
}

export const useAppStore = create<AppState>((set, get) => ({
  ...defaultState,

  setApiUrl: (url) => {
    set({ apiUrl: url })
    get().persistToLocalStorage()
  },

  setDirection: (direction) => {
    set({ direction })
    get().persistToLocalStorage()
  },

  setFormal: (formal) => {
    set({ formal })
    get().persistToLocalStorage()
  },

  setMaxNewTokens: (tokens) => {
    set({ maxNewTokens: tokens })
    get().persistToLocalStorage()
  },

  setGlossaryText: (text) => {
    set({ glossaryText: text })
    get().persistToLocalStorage()
  },

  setActiveTab: (tab) => {
    set({ activeTab: tab })
  },

  setIsTranslating: (isTranslating) => {
    set({ isTranslating })
  },

  setLastLatencyMs: (latency) => {
    set({ lastLatencyMs: latency })
  },

  setLastError: (error) => {
    set({ lastError: error, lastSuccess: null })
  },

  setLastSuccess: (message) => {
    set({ lastSuccess: message, lastError: null })
  },

  setHealth: (health) => {
    set({ health })
  },

  setInfo: (info) => {
    set({ info })
  },

  loadFromLocalStorage: () => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY)
      if (stored) {
        const parsed = JSON.parse(stored)
        set({
          apiUrl: parsed.apiUrl ?? defaultState.apiUrl,
          direction: parsed.direction ?? defaultState.direction,
          formal: parsed.formal ?? defaultState.formal,
          maxNewTokens: parsed.maxNewTokens ?? defaultState.maxNewTokens,
          glossaryText: parsed.glossaryText ?? defaultState.glossaryText,
        })
      }
    } catch (error) {
      console.error('Error loading from localStorage:', error)
    }
  },

  persistToLocalStorage: () => {
    try {
      const state = get()
      const toStore = {
        apiUrl: state.apiUrl,
        direction: state.direction,
        formal: state.formal,
        maxNewTokens: state.maxNewTokens,
        glossaryText: state.glossaryText,
      }
      localStorage.setItem(STORAGE_KEY, JSON.stringify(toStore))
    } catch (error) {
      console.error('Error saving to localStorage:', error)
    }
  },
}))

