# Operaciones y Despliegue en Producción

Este documento está dirigido a equipos de operaciones, DevOps y SRE que necesitan desplegar, monitorear y mantener el servicio de traducción en producción.

## 📋 Pre-requisitos del Sistema

### Recursos Mínimos Requeridos

| Componente | Mínimo | Recomendado | Dependencias |
|------------|--------|-------------|--------------|
| **CPU** | 2 cores | 4+ cores | Más cores = mejor throughput |
| **RAM** | 8 GB | 16 GB | Modelo 600M: 8GB, Modelo 1.3B: 16GB |
| **Disco** | 5 GB libres | 20 GB | Modelos + logs + cache |
| **Red** | Solo local | - | 100% offline después del setup |

### Límites Operacionales

```yaml
# Configuración conservadora por defecto
MAX_INPUT_TOKENS: 4096        # Ajustable según RAM disponible
DEFAULT_MAX_NEW_TOKENS: 1024  # Conservador para estabilidad
MAX_MAX_NEW_TOKENS: 8192      # Límite máximo anti-truncado
REQUEST_TIMEOUT: 300          # 5 minutos máximo por request
MAX_BATCH_SIZE: 16            # Tamaño de lote máximo
CT2_INTER_THREADS: 4          # Threads inter-request
CT2_INTRA_THREADS: 4          # Threads intra-request
```

### Escalabilidad Horizontal

- **1 instancia**: 10-50 requests/minuto (textos medianos)
- **Load balancer**: Nginx/HAProxy con health checks `/health`
- **Distribución**: Cada instancia mantiene su propio cache
- **Persistencia**: No requiere BD - cache solo en memoria

## 🚀 Despliegue

### Opción 1: Docker (Recomendado)

```bash
# 1. Preparación
make download     # Descargar modelos
make convert      # Convertir a CT2

# 2. Construcción
make docker-build

# 3. Despliegue local
make docker-run

# 4. Despliegue en cluster
docker run -d \
  --name traductor-prod \
  --restart unless-stopped \
  -p 8000:8000 \
  -v ./models:/models:ro \
  -e MAX_INPUT_TOKENS=4096 \
  -e DEFAULT_MAX_NEW_TOKENS=1024 \
  --memory=8g \
  --cpus=2 \
  traductor-es-da:latest
```

### Opción 2: Kubernetes

```yaml
# k8s-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: traductor-es-da
spec:
  replicas: 2
  selector:
    matchLabels:
      app: traductor-es-da
  template:
    metadata:
      labels:
        app: traductor-es-da
    spec:
      containers:
      - name: traductor
        image: traductor-es-da:latest
        ports:
        - containerPort: 8000
        resources:
          requests:
            memory: "8Gi"
            cpu: "2"
          limits:
            memory: "16Gi"
            cpu: "4"
        env:
        - name: MAX_INPUT_TOKENS
          value: "4096"
        - name: LOG_TRANSLATIONS
          value: "false"
        volumeMounts:
        - name: models
          mountPath: /models
          readOnly: true
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 90
          periodSeconds: 30
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
      volumes:
      - name: models
        persistentVolumeClaim:
          claimName: models-pvc
```

### Opción 3: Host Local

```bash
# 1. Setup del entorno
make venv
source venv/bin/activate

# 2. Configuración de producción
cp .env.example .env.prod
# Editar .env.prod con valores de producción

# 3. Instalación de modelos
make download
make convert

# 4. Inicio con systemd
sudo cp scripts/traductor.service /etc/systemd/system/
sudo systemctl enable traductor
sudo systemctl start traductor
```

## 📊 Monitoreo y Observabilidad

### Endpoints de Salud

```bash
# Estado del servicio
GET /health
# Respuesta: 200 OK con model_loaded=true/false

# Información detallada y métricas
GET /info
# Incluye: uptime, cache stats, límites, configuración
```

### Métricas Clave a Monitorear

| Métrica | Threshold | Acción |
|---------|-----------|---------|
| **Uptime** | > 99.5% | Alerta si < 99% |
| **Response time** | < 5s promedio | Escalar si > 10s |
| **Memory usage** | < 80% | Alerta si > 90% |
| **CPU usage** | < 70% promedio | Alerta si > 85% |
| **Cache hit rate** | > 60% | Investigar si < 30% |

### Logs Estructurados

```json
{
  "timestamp": "2025-01-XX",
  "level": "INFO",
  "message": "Translation completed",
  "latency_ms": 1250,
  "input_length": 342,
  "output_length": 389,
  "direction": "es-da",
  "cache_hit": true
}
```

**Importante**: Los logs NO incluyen contenido de traducción por privacidad.

### Alertas Recomendadas

```yaml
# Prometheus alerting rules
- alert: TraductorDown
  expr: up{job="traductor"} == 0
  for: 1m
  labels:
    severity: critical

- alert: TraductorHighLatency
  expr: traductor_request_duration_ms > 10000
  for: 5m
  labels:
    severity: warning

- alert: TraductorHighMemory
  expr: process_resident_memory_bytes / 1024 / 1024 / 1024 > 12
  for: 10m
  labels:
    severity: warning
```

## 🔒 Seguridad en Producción

### Configuración de Red

```bash
# Aislamiento completo (air-gapped)
docker run --network none traductor-es-da

# Acceso local únicamente
docker run -p 127.0.0.1:8000:8000 traductor-es-da

# Con reverse proxy (Nginx)
upstream traductor {
    server 127.0.0.1:8000;
}

server {
    listen 443 ssl;
    server_name traducciones.internal.company.com;
    
    location / {
        proxy_pass http://traductor;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### Variables de Entorno Seguras

```bash
# .env.prod
LOG_TRANSLATIONS=false          # CRÍTICO: No loguear contenido
LOG_LEVEL=INFO                  # Balance entre info y privacidad
HOST=127.0.0.1                 # Solo localhost en producción
MAX_BATCH_SIZE=8               # Reducir para evitar DoS
REQUEST_TIMEOUT=180            # 3 minutos máximo
```

### Auditoría de Seguridad

```bash
# Escaneo de dependencias (semanal)
make security

# Verificación de configuración
curl -I http://localhost:8000/health
# Verificar headers de seguridad en respuesta

# Test de penetración básico
nmap -p 8000 localhost
```

## 🔧 Mantenimiento

### Actualizaciones

```bash
# 1. Backup de modelos
cp -r models/ models.backup/

# 2. Update de código
git pull origin main
make docker-build

# 3. Rolling update (con zero-downtime)
docker stop traductor-old
docker run -d --name traductor-new traductor-es-da:latest
# Verificar health check antes de eliminar old

# 4. Rollback si necesario
docker stop traductor-new
docker start traductor-old
```

### Limpieza de Cache

```bash
# Limpiar cache vía API
curl -X POST http://localhost:8000/cache/clear

# Limpiar cache del sistema (si necesario)
docker exec traductor-prod python -c "
from app.cache import translation_cache
translation_cache.clear()
"
```

### Rotación de Logs

```bash
# systemd journal (si usando systemd)
journalctl -u traductor --rotate --vacuum-time=7d

# Docker logs
docker logs traductor-prod > logs/traductor-$(date +%Y%m%d).log
```

## 🚨 Troubleshooting

### Problemas Comunes

| Síntoma | Causa | Solución |
|---------|-------|----------|
| 503 Service Unavailable | Modelo no cargado | Verificar paths, reiniciar servicio |
| Alto uso de memoria | Cache creciendo sin límite | Reiniciar o limpiar cache |
| Requests lentos | CPU saturado | Ajustar threads o escalar |
| Traducción truncada | Límites muy bajos | Aumentar MAX_MAX_NEW_TOKENS |

### Comandos de Diagnóstico

```bash
# Estado del modelo
curl http://localhost:8000/health | jq

# Métricas detalladas
curl http://localhost:8000/info | jq

# Test de carga básico
for i in {1..10}; do
  curl -X POST http://localhost:8000/translate \
    -H "Content-Type: application/json" \
    -d '{"text": "Test de carga", "direction": "es-da"}' &
done

# Uso de recursos
docker stats traductor-prod
```

### Logs Útiles

```bash
# Buscar errores
grep -i error /var/log/traductor.log

# Buscar requests lentos
grep "Translation completed" logs/ | awk '$NF > 5000 {print}'

# Monitorear memoria
docker exec traductor-prod ps aux | grep python
```

## 📈 Performance Tuning

### Optimización por Hardware

```bash
# CPU intensivo (más cores)
CT2_INTER_THREADS=8
CT2_INTRA_THREADS=8

# Memoria limitada (reducir batch)
MAX_BATCH_SIZE=4
DEFAULT_MAX_NEW_TOKENS=512

# Alta latencia aceptable (calidad máxima)
BEAM_SIZE=5
MAX_MAX_NEW_TOKENS=10240
```

### Profiling

```bash
# Perfil de memoria
python -m memory_profiler app/app.py

# Perfil de CPU
python -m cProfile -o profile.prof start_server.py
```

Este documento debe actualizarse según la evolución del servicio y los patrones de uso observados en producción.
