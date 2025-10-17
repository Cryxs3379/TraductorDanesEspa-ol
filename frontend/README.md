# Frontend - Traductor ES ↔ DA

Frontend profesional en React para el traductor bidireccional Español ↔ Danés, 100% local y offline.

## 🚀 Stack Tecnológico

- **Build**: Vite + TypeScript
- **UI**: React + Tailwind CSS + shadcn/ui
- **Estado**: Zustand (ligero y performante)
- **Validación**: Zod
- **HTTP**: Fetch API con timeout (`AbortController`)
- **Iconos**: Lucide React
- **Tests**: Vitest
- **Linting**: ESLint + Prettier

## 📋 Características

### ✅ Funcionalidades principales

- **Bidireccionalidad**: Soporte completo para ES→DA y DA→ES
- **Dos modos de traducción**:
  - Texto plano (segmentado automáticamente)
  - HTML (preserva estructura y atributos)
- **Glosario personalizable**:
  - Editor de pares término_origen=término_destino
  - Importar/Exportar archivos `.txt`
  - Persistido en `localStorage`
- **Estilo formal danés**: Switch para activar "De/Dem" (solo ES→DA)
- **Métricas en tiempo real**:
  - Estado del backend (`/health`)
  - Latencia por request
  - Estadísticas de caché (hits/misses)
  - Uptime del servidor
- **Manejo robusto de errores**:
  - 503 → "Modelo cargando, inténtalo de nuevo en unos segundos"
  - 422 → "Entrada/salida inválida. Reduce el texto o revisa el HTML"
  - Timeout (60s) → "La petición tardó demasiado. Divide el texto o reduce max tokens"
- **Experiencia de usuario**:
  - Contador de caracteres
  - Copiar/Guardar resultados
  - Atajos de teclado (Ctrl/⌘+Enter para traducir)
  - Persistencia en `localStorage` (API URL, dirección, formal, glosario)
  - Vista previa HTML sanitizada

### 🔒 Privacidad y Seguridad

- **100% local**: Sin llamadas a servicios externos
- **Sin analytics ni telemetría**
- **Sin tracking de usuarios**
- **HTML sanitizado** en vista previa (protección XSS)

### ♿ Accesibilidad

- Labels y roles ARIA correctos
- Navegación por teclado
- Focus visible
- Contraste de colores adecuado
- Mensajes de error claros y legibles

## 🛠️ Instalación y Uso

### Requisitos previos

- Node.js 18+ (recomendado: 20 LTS)
- Backend corriendo en `http://localhost:8000` (ver README principal del repositorio)

### Instalación

```bash
cd frontend
npm install
```

### Desarrollo

```bash
npm run dev
```

La aplicación estará disponible en `http://localhost:5173`.

### Build para producción

```bash
npm run build
```

Los archivos estáticos se generarán en `frontend/dist/`.

### Vista previa de producción

```bash
npm run preview
```

### Tests

```bash
npm run test
```

### Linting y formato

```bash
# Lint
npm run lint

# Formato con Prettier
npm run format
```

## 📁 Estructura del Proyecto

```
frontend/
├── index.html                 # HTML principal
├── package.json               # Dependencias y scripts
├── vite.config.ts             # Configuración de Vite
├── tsconfig.json              # Configuración de TypeScript
├── tailwind.config.ts         # Configuración de Tailwind CSS
├── postcss.config.js          # PostCSS (Tailwind)
├── .eslintrc.cjs              # ESLint
├── .prettierrc                # Prettier
├── README.md                  # Este archivo
└── src/
    ├── main.tsx               # Punto de entrada de React
    ├── App.tsx                # Componente raíz
    ├── styles/
    │   └── globals.css        # Estilos globales (Tailwind)
    ├── lib/
    │   ├── types.ts           # Tipos TypeScript (API requests/responses)
    │   ├── api.ts             # Cliente REST con timeout y manejo de errores
    │   ├── zod-schemas.ts     # Validaciones de formularios
    │   └── utils.ts           # Utilidades (cn, parseGlossary, etc.)
    ├── store/
    │   └── useAppStore.ts     # Store de Zustand (config, estado, persistencia)
    ├── hooks/
    │   └── useTranslate.ts    # Hook de lógica de traducción
    ├── components/
    │   ├── ui/                # Componentes shadcn/ui
    │   │   ├── button.tsx
    │   │   ├── input.tsx
    │   │   ├── textarea.tsx
    │   │   ├── label.tsx
    │   │   ├── select.tsx
    │   │   ├── switch.tsx
    │   │   ├── tabs.tsx
    │   │   ├── dialog.tsx
    │   │   └── tooltip.tsx
    │   ├── DirectionSelect.tsx    # Selector ES→DA / DA→ES
    │   ├── ApiUrlInput.tsx        # Input + botón "Probar conexión"
    │   ├── GlossaryPanel.tsx      # Editor de glosario (Dialog)
    │   ├── MetricsBar.tsx         # Barra de métricas (footer)
    │   ├── ErrorBanner.tsx        # Banner de errores/éxito
    │   ├── CopyButtons.tsx        # Botones Copiar/Guardar
    │   ├── TextTranslator.tsx     # Panel de traducción de texto
    │   └── HtmlTranslator.tsx     # Panel de traducción HTML
    └── pages/
        └── Home.tsx               # Página principal
```

## 🔌 Integración con el Backend

El frontend se comunica con la API FastAPI del backend mediante los siguientes endpoints:

### Endpoints utilizados

| Endpoint | Método | Descripción |
|----------|--------|-------------|
| `/translate` | POST | Traducir texto plano |
| `/translate/html` | POST | Traducir HTML |
| `/health` | GET | Estado del servicio y modelo |
| `/info` | GET | Métricas (caché, uptime, versión) |

### Configuración de la API URL

Por defecto, el frontend usa `http://localhost:8000` como URL del backend. Puedes cambiarla desde la interfaz:

1. En el campo "URL del backend" en el header
2. Pulsa "Probar" para verificar la conexión
3. La configuración se guarda automáticamente en `localStorage`

### CORS

El backend ya está configurado para aceptar requests desde:
- `file://` (para abrir el HTML directamente)
- `http://localhost:*` (desarrollo)
- `http://127.0.0.1:*` (desarrollo)

## 📝 Uso

### 1. Traducción de texto

1. Selecciona la dirección (ES→DA o DA→ES)
2. Escribe o pega el texto en el panel izquierdo
3. (Opcional) Activa el estilo "Formal" para danés (solo ES→DA)
4. (Opcional) Configura un glosario desde el botón "Glosario"
5. Pulsa "Traducir" o usa `Ctrl+Enter`
6. La traducción aparecerá en el panel derecho
7. Usa "Copiar" o "Guardar" para exportar el resultado

### 2. Traducción de HTML (correos)

1. Cambia a la pestaña "Correo (HTML)"
2. Pega el código HTML en el panel izquierdo
3. Configura dirección, formal y glosario si es necesario
4. Pulsa "Traducir HTML"
5. Visualiza el resultado en modo "Código" o "Vista previa"
6. Usa "Copiar" o "Guardar" para exportar

### 3. Glosario

Formato: `término_origen=término_destino` (una línea por término).

**Ejemplo ES→DA**:
```
computadora=computer
sistema operativo=operativsystem
correo electrónico=e-mail
```

**Ejemplo DA→ES**:
```
computer=computadora
operativsystem=sistema operativo
e-mail=correo electrónico
```

Puedes importar/exportar archivos `.txt` desde el editor.

### 4. Métricas

La barra inferior muestra:
- **Estado**: 🟢 Listo / 🟡 Cargando / 🔴 Offline
- **Latencia**: Tiempo de respuesta del último request (ms)
- **Cache**: Porcentaje de hits, número de hits y entradas en caché
- **Uptime**: Tiempo que el backend lleva corriendo

Pulsa el botón "🔄" para refrescar las métricas manualmente.

## 🧪 Tests

Los tests cubren:

- **Cliente API** (`api.test.ts`):
  - Traducción exitosa
  - Manejo de errores 503/422
  - Timeout con `AbortController`
  - Health check
  - Traducción HTML

Para ejecutar los tests:

```bash
npm run test
```

Para ejecutar en modo watch:

```bash
npm run test -- --watch
```

## 🎨 Personalización

### Cambiar tema (dark/light)

El proyecto usa las CSS variables de shadcn/ui definidas en `src/styles/globals.css`. Puedes personalizar los colores modificando las variables en `:root` y `.dark`.

### Agregar nuevos componentes shadcn/ui

Si necesitas más componentes de shadcn/ui, puedes copiarlos desde [ui.shadcn.com](https://ui.shadcn.com) y adaptarlos a la estructura del proyecto.

## 📦 Build y Despliegue

### Build local

```bash
npm run build
```

Esto genera los archivos optimizados en `frontend/dist/`.

### Servir desde el backend FastAPI

El backend puede servir el frontend estático en producción. Para ello:

1. Crea el build: `npm run build`
2. En el backend (`app/app.py`), monta los archivos estáticos:

```python
from fastapi.staticfiles import StaticFiles

app.mount("/", StaticFiles(directory="frontend/dist", html=True), name="frontend")
```

3. Accede a `http://localhost:8000/` para usar el frontend servido desde FastAPI.

## 🐛 Solución de Problemas

### Error: "No se pudo conectar al backend"

- Verifica que el backend esté corriendo en `http://localhost:8000`
- Ejecuta `GET /health` desde el navegador o Postman para confirmar
- Revisa la URL configurada en el campo "URL del backend"

### Error: "Modelo cargando, inténtalo de nuevo en unos segundos"

- El modelo NLLB está cargando en memoria. Espera 10-30 segundos.
- Verifica el estado en la barra de métricas (🟡 Cargando → 🟢 Listo)

### Timeout en traducciones largas

- Divide el texto en secciones más pequeñas (el backend segmenta automáticamente, pero textos enormes pueden tardar)
- Reduce el valor de `max_new_tokens` si es necesario

### Vista previa HTML no se muestra correctamente

- Asegúrate de que el HTML de entrada sea válido
- El backend sanitiza el HTML por seguridad; algunos tags/atributos pueden eliminarse

## 📄 Licencia

Este frontend es parte del proyecto "Traductor ES ↔ DA" y comparte la misma licencia que el proyecto principal.

## 🤝 Contribuciones

Las contribuciones son bienvenidas. Por favor:

1. Fork el repositorio
2. Crea una rama para tu feature (`git checkout -b feature/nueva-funcionalidad`)
3. Commit tus cambios (`git commit -m 'feat: añadir nueva funcionalidad'`)
4. Push a la rama (`git push origin feature/nueva-funcionalidad`)
5. Abre un Pull Request

Asegúrate de:
- Ejecutar `npm run lint` y `npm run format` antes de commit
- Ejecutar `npm run test` para verificar que los tests pasen
- Seguir las convenciones de código del proyecto

