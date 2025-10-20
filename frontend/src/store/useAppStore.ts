import { create } from 'zustand'
import type { Direction, TranslationMode, HealthResponse, InfoResponse } from '@/lib/types'

interface AppState {
  // Configuración
  apiUrl: string
  direction: Direction
  formal: boolean
  maxTokensMode: 'auto' | 'manual'  // modo de tokens: auto-calculado o manual
  maxNewTokens: number              // solo usado si mode='manual' (32-512)
  strictMax: boolean                // solo usado si mode='manual'
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
  setMaxTokensMode: (mode: 'auto' | 'manual') => void
  setMaxNewTokens: (tokens: number) => void
  setStrictMax: (strict: boolean) => void
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
  maxTokensMode: 'auto' as 'auto' | 'manual',  // por defecto auto-calculado
  maxNewTokens: 256,  // usado solo en modo manual
  strictMax: false,   // por defecto permitir elevación server-side
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

  setMaxTokensMode: (mode) => {
    set({ maxTokensMode: mode })
    get().persistToLocalStorage()
  },

  setMaxNewTokens: (tokens) => {
    set({ maxNewTokens: Math.max(32, Math.min(512, tokens)) })  // clamp 32-512
    get().persistToLocalStorage()
  },

  setStrictMax: (strict) => {
    set({ strictMax: strict })
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
        
        // Migración: si existe maxNewTokens con valor 192 (viejo default),
        // o si no existe maxTokensMode, resetear a defaults nuevos
        const needsMigration = 
          parsed.maxNewTokens === 192 ||
          parsed.maxTokensMode === undefined
        
        if (needsMigration) {
          console.log('Migrando configuración antigua de tokens a modo Auto')
          set({
            apiUrl: parsed.apiUrl ?? defaultState.apiUrl,
            direction: parsed.direction ?? defaultState.direction,
            formal: parsed.formal ?? defaultState.formal,
            maxTokensMode: 'auto',
            maxNewTokens: 256,
            strictMax: false,
            glossaryText: parsed.glossaryText ?? defaultState.glossaryText,
          })
          // Persistir la configuración migrada
          get().persistToLocalStorage()
        } else {
          // Carga normal
          set({
            apiUrl: parsed.apiUrl ?? defaultState.apiUrl,
            direction: parsed.direction ?? defaultState.direction,
            formal: parsed.formal ?? defaultState.formal,
            maxTokensMode: parsed.maxTokensMode ?? defaultState.maxTokensMode,
            maxNewTokens: parsed.maxNewTokens ?? defaultState.maxNewTokens,
            strictMax: parsed.strictMax ?? defaultState.strictMax,
            glossaryText: parsed.glossaryText ?? defaultState.glossaryText,
          })
        }
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
        maxTokensMode: state.maxTokensMode,
        maxNewTokens: state.maxNewTokens,
        strictMax: state.strictMax,
        glossaryText: state.glossaryText,
      }
      localStorage.setItem(STORAGE_KEY, JSON.stringify(toStore))
    } catch (error) {
      console.error('Error saving to localStorage:', error)
    }
  },
}))

