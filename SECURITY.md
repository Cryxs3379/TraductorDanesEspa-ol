# Seguridad y Privacidad

Este documento describe las medidas de seguridad implementadas en el traductor ES↔DA y las mejores prácticas para mantener la privacidad y seguridad en entornos corporativos.

## 🔒 Principios de Seguridad

### 1. Privacidad por Diseño

- **100% Offline**: No hay llamadas a servicios externos después del setup inicial
- **Sin Telemetría**: No se envían datos a servidores externos
- **Sin Logging de Contenido**: Los textos de usuario nunca se registran en logs
- **Cache Local**: Todas las traducciones se almacenan solo en memoria local

### 2. Configuración Segura por Defecto

```bash
# Variables críticas para privacidad
LOG_TRANSLATIONS=false    # ¡CRÍTICO! No cambiar a true en producción
LOG_LEVEL=INFO           # Balance entre observabilidad y privacidad
HOST=127.0.0.1          # Solo localhost por defecto
allow_credentials=False  # CORS sin credenciales
```

## 🛡️ Medidas de Seguridad Implementadas

### Seguridad de Entrada (Input Security)

#### Sanitización HTML

```python
# app/utils_html.py - Sanitización centralizada
def sanitize_html(html_content: str) -> str:
    # Elimina scripts, iframes, objetos embebidos
    # Permite solo etiquetas seguras para emails/correos
    # Valida URLs en href/src para evitar javascript:
```

**Etiquetas permitidas**: `p`, `br`, `strong`, `em`, `a`, `img`, `ul`, `ol`, `li`, `table`, etc.
**Etiquetas bloqueadas**: `script`, `style`, `iframe`, `object`, `embed`

#### Validación de Entrada

```python
# app/schemas.py - Validación estricta con Pydantic
class TranslateRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=50000)
    max_new_tokens: Optional[int] = Field(ge=32, le=10000)
    # ... más validaciones
```

### Seguridad de Salida (Output Security)

#### Cabeceras de Seguridad

```python
# Headers automáticos en todas las respuestas
response.headers["X-Content-Type-Options"] = "nosniff"
response.headers["X-Frame-Options"] = "DENY"
response.headers["X-XSS-Protection"] = "1; mode=block"
response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
```

#### Control de Cache

```python
# Cache control específico por endpoint
if request.url.path.startswith(("/translate", "/info")):
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, private"
```

### Seguridad de Red

#### CORS Configurado

```python
# Configuración restrictiva de CORS
allow_origins=["*", "null"]  # Solo para desarrollo local
allow_methods=["GET", "POST", "OPTIONS"]  # Métodos limitados
allow_headers=["Content-Type", "Authorization", "Accept"]  # Headers limitados
allow_credentials=False  # Crítico para seguridad
```

#### Aislamiento de Red

```bash
# Modo air-gapped (sin red)
docker run --network none traductor-es-da

# Solo localhost
docker run -p 127.0.0.1:8000:8000 traductor-es-da
```

## 🔐 Privacidad de Datos

### Política de No-Logging

**NUNCA se registra en logs**:
- Textos de entrada del usuario
- Traducciones generadas
- Contenido de HTML
- Datos de glosarios personalizados

**SÍ se registra** (métricas agregadas):
- Tiempo de respuesta
- Longitud de entrada/salida
- Hits/misses de cache
- Errores técnicos (sin contenido)

### Manejo de Cache

```python
# Cache LRU con límite estricto
MAX_CACHE_SIZE = 1024  # Máximo 1024 entradas
# Solo en memoria, no persistente
# Se limpia al reiniciar el servicio
```

### Limpieza Automática

```bash
# Endpoint para limpiar cache
POST /cache/clear

# Limpieza automática en reinicio
# No hay persistencia de datos de usuario
```

## 🚨 Evaluación de Riesgos

### Riesgos Identificados y Mitigaciones

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|--------------|---------|------------|
| **Fuga de datos** | Baja | Alto | 100% offline, no logging |
| **DoS por texto largo** | Media | Medio | Límites de entrada, timeouts |
| **XSS en HTML** | Baja | Medio | Sanitización HTML centralizada |
| **Acceso no autorizado** | Baja | Alto | CORS restrictivo, solo localhost |

### Amenazas Específicas

#### 1. **Inyección de Contenido Malicioso**

**Mitigación**:
```python
# Sanitización de HTML antes del procesamiento
sanitized_html = sanitize_html(user_html)
# Validación de URLs en enlaces/imágenes
if not _is_safe_url(url): url = None
```

#### 2. **Ataques de Denegación de Servicio**

**Mitigación**:
```python
# Límites estrictos
MAX_BATCH_SIZE = 16
REQUEST_TIMEOUT = 300  # 5 minutos
MAX_INPUT_TOKENS = 4096
```

#### 3. **Fuga de Información por Logs**

**Mitigación**:
```python
# Verificación estricta
if not settings.LOG_TRANSLATIONS:
    logger.info(f"Processing request length: {len(text)}")
    # NUNCA: logger.info(f"Text: {text}")  # ¡PROHIBIDO!
```

## 🔍 Auditoría y Cumplimiento

### Checklist de Seguridad

#### Pre-Despliegue

- [ ] `LOG_TRANSLATIONS=false` verificado
- [ ] CORS configurado correctamente
- [ ] Headers de seguridad presentes
- [ ] Límites de entrada configurados
- [ ] Sanitización HTML activa
- [ ] Tests de seguridad ejecutados

#### Post-Despliegue

- [ ] Endpoint `/health` responde correctamente
- [ ] Headers de seguridad en respuestas HTTP
- [ ] No se observa contenido en logs
- [ ] Cache funciona correctamente
- [ ] Timeouts funcionan según especificación

### Escaneo Automático

```bash
# Auditoría de dependencias (CI/CD)
make security

# Verificación de configuración
curl -I http://localhost:8000/health

# Test de penetración básico
# (usar herramientas como OWASP ZAP en entorno de testing)
```

### Cumplimiento

#### GDPR/Privacidad

✅ **Datos mínimos**: Solo se procesa lo necesario para la traducción
✅ **Sin transferencias**: 100% local, sin envío de datos externos  
✅ **Derecho al olvido**: Cache se limpia automáticamente
✅ **Transparencia**: Documentación clara de qué se procesa

#### ISO 27001/SOC 2

✅ **Control de acceso**: CORS restrictivo, solo localhost
✅ **Cifrado**: HTTPS recomendado en producción
✅ **Monitoreo**: Logs de seguridad sin contenido
✅ **Respuesta a incidentes**: Documentación de troubleshooting

## 🔧 Configuración Segura por Entorno

### Desarrollo

```bash
# .env.development
LOG_TRANSLATIONS=false  # NUNCA true, ni en desarrollo
HOST=127.0.0.1
CORS_ORIGINS=["http://localhost:5173"]
```

### Testing

```bash
# .env.testing  
LOG_TRANSLATIONS=false
MAX_BATCH_SIZE=4  # Reducido para tests
REQUEST_TIMEOUT=60  # Más corto para CI
```

### Producción

```bash
# .env.production
LOG_TRANSLATIONS=false  # CRÍTICO
LOG_LEVEL=WARNING  # Menos verbose
HOST=127.0.0.1     # Solo localhost
MAX_BATCH_SIZE=8   # Conservador
REQUEST_TIMEOUT=180  # 3 minutos máximo
```

## 🚨 Respuesta a Incidentes

### Procedimiento de Emergencia

1. **Identificación**
   ```bash
   # Verificar logs de error
   docker logs traductor-prod --tail 100
   curl http://localhost:8000/health
   ```

2. **Contención**
   ```bash
   # Detener servicio si es necesario
   docker stop traductor-prod
   # Bloquear acceso de red si hay compromiso
   ```

3. **Análisis**
   ```bash
   # Revisar configuración
   docker exec traductor-prod env | grep LOG_TRANSLATIONS
   # Verificar cabeceras de seguridad
   curl -I http://localhost:8000/health
   ```

4. **Recuperación**
   ```bash
   # Limpiar cache
   curl -X POST http://localhost:8000/cache/clear
   # Reiniciar con configuración segura
   docker restart traductor-prod
   ```

### Contactos de Seguridad

- **Equipo de Desarrollo**: Para issues técnicos
- **Equipo de Seguridad**: Para vulnerabilidades críticas  
- **Equipo de Operaciones**: Para incidentes de infraestructura

---

**⚠️ IMPORTANTE**: Este documento debe revisarse periódicamente y actualizarse según las mejores prácticas de seguridad y cambios en el código.
