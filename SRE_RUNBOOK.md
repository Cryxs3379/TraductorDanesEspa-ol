# SRE Runbook - Traductor ES↔DA

Este runbook proporciona procedimientos rápidos para diagnosticar y resolver problemas comunes en el servicio de traducción ES↔DA en producción.

## 🚨 Procedimientos de Emergencia

### Health Check Rápido

```bash
# Verificación básica del estado
curl -s http://localhost:8000/health | jq

# Respuestas esperadas:
# ✅ {"status": "healthy", "model_loaded": true}
# ❌ {"status": "unhealthy", "model_loaded": false}
```

### Diagnóstico en 30 Segundos

```bash
#!/bin/bash
# quick-diagnosis.sh

echo "=== DIAGNÓSTICO RÁPIDO ==="
echo

# 1. Servicio responde?
echo "1. Health check..."
if curl -s http://localhost:8000/health > /dev/null; then
    echo "   ✅ Servicio responde"
else
    echo "   ❌ Servicio no responde - REINICIAR"
    exit 1
fi

# 2. Modelo cargado?
MODEL_LOADED=$(curl -s http://localhost:8000/health | jq -r '.model_loaded')
if [ "$MODEL_LOADED" = "true" ]; then
    echo "   ✅ Modelo cargado"
else
    echo "   ❌ Modelo no cargado - REVISAR LOGS"
fi

# 3. Métricas básicas
echo "2. Métricas..."
curl -s http://localhost:8000/info | jq '.uptime, .cache.size, .cache.hit_rate'

echo "=== FIN DIAGNÓSTICO ==="
```

## 🔍 Problemas Comunes

### 1. **503 Service Unavailable**

**Síntoma**: `{"detail": "El modelo está cargando..."}`

**Diagnóstico**:
```bash
# Verificar estado del modelo
curl -s http://localhost:8000/health | jq '.model_loaded'

# Revisar logs de carga
docker logs traductor-prod --tail 50 | grep -i "modelo\|load"
```

**Soluciones**:
```bash
# Opción 1: Esperar (carga puede tardar 1-2 minutos)
sleep 60 && curl http://localhost:8000/health

# Opción 2: Reiniciar si tarda mucho
docker restart traductor-prod

# Opción 3: Verificar archivos del modelo
docker exec traductor-prod ls -la /models/
```

### 2. **Traducciones Truncadas**

**Síntoma**: Traducción muy corta o incompleta

**Diagnóstico**:
```bash
# Verificar configuración de límites
curl -s http://localhost:8000/info | jq '.limits'

# Test rápido con texto largo
curl -X POST http://localhost:8000/translate \
  -H "Content-Type: application/json" \
  -d '{"text": "Texto largo de prueba. " + " repetido 100 veces", "direction": "es-da"}'
```

**Solución**:
```bash
# Aumentar límites si es necesario
docker run -e MAX_MAX_NEW_TOKENS=8192 traductor-prod
```

### 3. **Alta Latencia**

**Síntoma**: Requests tardan >10 segundos

**Diagnóstico**:
```bash
# Verificar uso de recursos
docker stats traductor-prod --no-stream

# Revisar métricas
curl -s http://localhost:8000/info | jq '.performance'
```

**Soluciones**:
```bash
# Opción 1: Limpiar cache
curl -X POST http://localhost:8000/cache/clear

# Opción 2: Ajustar threads
docker run -e CT2_INTER_THREADS=8 traductor-prod

# Opción 3: Reducir batch size
docker run -e MAX_BATCH_SIZE=4 traductor-prod
```

### 4. **Alto Uso de Memoria**

**Síntoma**: Memory usage >90%

**Diagnóstico**:
```bash
# Verificar uso de memoria
docker stats traductor-prod --no-stream

# Verificar tamaño de cache
curl -s http://localhost:8000/info | jq '.cache'
```

**Solución**:
```bash
# Limpiar cache
curl -X POST http://localhost:8000/cache/clear

# Si persiste, reiniciar
docker restart traductor-prod
```

## 📊 Monitoreo Continuo

### Script de Monitoreo

```bash
#!/bin/bash
# monitor.sh - Ejecutar cada 5 minutos

ENDPOINT="http://localhost:8000"
LOG_FILE="/var/log/traductor-monitor.log"

# Health check
HEALTH=$(curl -s $ENDPOINT/health 2>/dev/null)
if [ $? -ne 0 ]; then
    echo "$(date): ERROR - Service not responding" >> $LOG_FILE
    # Enviar alerta
    exit 1
fi

# Verificar modelo
MODEL_LOADED=$(echo $HEALTH | jq -r '.model_loaded')
if [ "$MODEL_LOADED" != "true" ]; then
    echo "$(date): WARNING - Model not loaded" >> $LOG_FILE
fi

# Obtener métricas
INFO=$(curl -s $ENDPOINT/info 2>/dev/null)
if [ $? -eq 0 ]; then
    CACHE_SIZE=$(echo $INFO | jq -r '.cache.size')
    HIT_RATE=$(echo $INFO | jq -r '.cache.hit_rate')
    echo "$(date): Cache size: $CACHE_SIZE, Hit rate: $HIT_RATE" >> $LOG_FILE
fi
```

### Alertas Recomendadas

```yaml
# Prometheus rules
groups:
- name: traductor.rules
  rules:
  - alert: TraductorDown
    expr: up{job="traductor"} == 0
    for: 1m
    labels:
      severity: critical
    annotations:
      summary: "Traductor service is down"

  - alert: TraductorModelNotLoaded
    expr: traductor_model_loaded == 0
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "Traductor model is not loaded"

  - alert: TraductorHighLatency
    expr: histogram_quantile(0.95, traductor_request_duration_seconds) > 10
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "Traductor high latency detected"
```

## 🔧 Comandos Útiles

### Verificación Rápida

```bash
# Estado general
curl -s http://localhost:8000/health | jq

# Información detallada
curl -s http://localhost:8000/info | jq

# Test de funcionalidad
curl -X POST http://localhost:8000/translate \
  -H "Content-Type: application/json" \
  -d '{"text": "Hola mundo", "direction": "es-da"}' | jq

# Limpiar cache
curl -X POST http://localhost:8000/cache/clear | jq
```

### Logs Útiles

```bash
# Últimos errores
docker logs traductor-prod --tail 100 | grep -i error

# Logs de carga del modelo
docker logs traductor-prod | grep -i "modelo\|loaded\|startup"

# Logs de requests (sin contenido)
docker logs traductor-prod | grep "Translation completed"

# Búsqueda específica
docker logs traductor-prod --since 1h | grep "WARNING\|ERROR"
```

### Debugging Avanzado

```bash
# Entrar al contenedor
docker exec -it traductor-prod /bin/bash

# Verificar variables de entorno
docker exec traductor-prod env | grep -E "(LOG_|MAX_|CT2_)"

# Verificar archivos del modelo
docker exec traductor-prod ls -la /models/

# Test de conectividad interna
docker exec traductor-prod curl http://localhost:8000/health
```

## 🚨 Procedimientos de Escalación

### Nivel 1: Problemas Leves (5-15 min)
- Cache hit rate <30%
- Latencia >5s pero <15s
- Algunos requests fallan (<5%)

**Acciones**:
1. Limpiar cache
2. Verificar logs recientes
3. Revisar uso de recursos

### Nivel 2: Problemas Moderados (15-30 min)
- Modelo no cargado por >10 min
- Latencia >15s consistentemente
- 10-50% de requests fallan

**Acciones**:
1. Reiniciar servicio
2. Verificar configuración
3. Notificar al equipo de desarrollo

### Nivel 3: Problemas Críticos (30+ min)
- Servicio completamente caído
- 50%+ requests fallan
- Errores de memoria o CPU

**Acciones**:
1. Failover a instancia de backup
2. Contactar equipo de desarrollo inmediatamente
3. Documentar incidente para post-mortem

## 📋 Checklists de Diagnóstico

### Checklist Pre-Deployment

- [ ] Health endpoint responde 200
- [ ] Modelo cargado (model_loaded=true)
- [ ] Cache funcionando
- [ ] Headers de seguridad presentes
- [ ] Logs sin errores críticos
- [ ] Uso de memoria <80%
- [ ] CPU usage <70%

### Checklist Post-Incident

- [ ] Servicio restaurado
- [ ] Health checks pasando
- [ ] Funcionalidad básica verificada
- [ ] Logs monitoreados por 30 min
- [ ] Equipo notificado del estado
- [ ] Incidente documentado

---

**📞 Contactos de Emergencia**:
- **On-call Engineer**: [Definir según organización]
- **Escalation Manager**: [Definir según organización]
- **Product Team**: [Definir según organización]
