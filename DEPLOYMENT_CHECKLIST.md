# ✅ Checklist de Despliegue y Verificación

Usa esta lista para verificar que todo esté configurado correctamente.

---

## 📋 Pre-requisitos del Sistema

- [ ] **Sistema Operativo**: Windows 10+, Linux, o macOS
- [ ] **Python**: Versión 3.11 o superior instalada
- [ ] **RAM**: Mínimo 8 GB disponible (16 GB para modelo 1.3B)
- [ ] **Disco**: Mínimo 5 GB libres
- [ ] **Internet**: Para descarga inicial del modelo
- [ ] (Opcional) **Docker**: Si planeas usar containerización

---

## 🔧 Instalación Local

### 1. Preparación del Entorno

- [ ] Clonar o descomprimir el proyecto
- [ ] Abrir terminal en el directorio del proyecto
- [ ] Verificar que `requirements.txt` existe

### 2. Crear Entorno Virtual

```bash
make venv
```

- [ ] Comando ejecutado sin errores
- [ ] Carpeta `venv/` creada
- [ ] Dependencias instaladas (FastAPI, CTranslate2, etc.)

### 3. Verificar Sistema

```bash
python scripts/check_system.py
```

- [ ] Python 3.11+ detectado
- [ ] Todas las dependencias instaladas
- [ ] Espacio en disco suficiente
- [ ] RAM suficiente disponible

---

## 📥 Descarga y Conversión de Modelos

### 4. Descargar Modelo

```bash
make download
```

**Verificar**:
- [ ] Descarga completada sin errores
- [ ] Carpeta `models/nllb-600m/` existe
- [ ] Archivos dentro: `config.json`, `tokenizer.json`, `sentencepiece.bpe.model`, `pytorch_model.bin`
- [ ] Tamaño total: ~2.4 GB

**Tiempo estimado**: 5-20 minutos según conexión

### 5. Convertir a CTranslate2

```bash
make convert
```

**Verificar**:
- [ ] Conversión completada sin errores
- [ ] Carpeta `models/nllb-600m-ct2-int8/` existe
- [ ] Archivos dentro: `model.bin`, `shared_vocabulary.txt`, `config.json`
- [ ] Tamaño total: ~600 MB

**Tiempo estimado**: 2-5 minutos

---

## 🚀 Ejecución del Servicio

### 6. Iniciar Servidor

```bash
make run
```

**Verificar**:
- [ ] Servidor inicia sin errores
- [ ] Mensaje "✓ Modelo cargado exitosamente"
- [ ] Mensaje "✓ Warmup completado - Sistema listo"
- [ ] Logs muestran "Application startup complete"
- [ ] No hay errores de "modelo no encontrado"

### 7. Verificar Endpoints

**En otra terminal o navegador**:

- [ ] http://localhost:8000/ responde (info del servicio)
- [ ] http://localhost:8000/health responde `{"status": "healthy"}`
- [ ] http://localhost:8000/docs muestra Swagger UI
- [ ] http://localhost:8000/redoc muestra ReDoc

---

## 🧪 Pruebas Funcionales

### 8. Test Manual con cURL

```bash
make curl-test
```

**Verificar**:
- [ ] Devuelve JSON válido
- [ ] Campo `translations` contiene array
- [ ] Traducción no está vacía
- [ ] Campo `provider` es "nllb-ct2-int8"

### 9. Ejecutar Tests Automatizados

```bash
make test
```

**Verificar**:
- [ ] Todos los tests pasan (sin failures)
- [ ] Test de traducción simple pasa
- [ ] Test de traducción batch pasa
- [ ] Test con glosario pasa
- [ ] Health check test pasa

### 10. Probar con Swagger UI

Abrir http://localhost:8000/docs

- [ ] Interfaz Swagger carga correctamente
- [ ] Endpoint `/translate` visible
- [ ] Botón "Try it out" funciona
- [ ] Enviar request de prueba: `{"text": "Hola mundo"}`
- [ ] Response 200 con traducción válida

---

## 🐳 Despliegue Docker (Opcional)

### 11. Build Imagen Docker

```bash
make docker-build
```

**Verificar**:
- [ ] Build completa sin errores
- [ ] Imagen `traductor-es-da:latest` creada
- [ ] Tamaño de imagen razonable (~1-2 GB sin modelos)

### 12. Ejecutar Contenedor

```bash
make docker-run
```

**Verificar**:
- [ ] Contenedor inicia sin errores
- [ ] Volumen de modelos montado correctamente
- [ ] Puerto 8000 mapeado
- [ ] Logs muestran "✓ Modelo cargado"

### 13. Probar Contenedor Docker

```bash
curl http://localhost:8000/health
docker logs traductor-es-da
```

**Verificar**:
- [ ] Health endpoint responde
- [ ] Logs muestran startup exitoso
- [ ] No hay errores de "modelo no encontrado"

---

## 🎯 Pruebas de Funcionalidad Completa

### 14. Traducción Simple

```python
import requests
r = requests.post("http://localhost:8000/translate", json={"text": "Hola"})
assert r.status_code == 200
assert len(r.json()["translations"]) == 1
```

- [ ] Status 200
- [ ] Traducción no vacía

### 15. Traducción Batch

```python
r = requests.post("http://localhost:8000/translate", 
                  json={"text": ["Hola", "Adiós", "Gracias"]})
assert len(r.json()["translations"]) == 3
```

- [ ] Status 200
- [ ] 3 traducciones devueltas
- [ ] Todas no vacías

### 16. Glosario

```python
r = requests.post("http://localhost:8000/translate",
                  json={"text": "Python es genial",
                        "glossary": {"Python": "Python"}})
translation = r.json()["translations"][0]
```

- [ ] Status 200
- [ ] Traducción contiene "Python" preservado

### 17. Manejo de Errores

```python
# Texto vacío
r = requests.post("http://localhost:8000/translate", json={"text": ""})
assert r.status_code in [400, 422]

# max_new_tokens inválido
r = requests.post("http://localhost:8000/translate",
                  json={"text": "Hola", "max_new_tokens": 0})
assert r.status_code == 422
```

- [ ] Errores manejados correctamente
- [ ] Mensajes de error claros

---

## 📊 Pruebas de Performance

### 18. Latencia

```bash
time curl -X POST http://localhost:8000/translate \
  -H "Content-Type: application/json" \
  -d '{"text": "Hola mundo"}'
```

**Esperado**:
- [ ] Primera request: 1-3 segundos (warmup)
- [ ] Requests subsecuentes: < 2 segundos

### 19. Throughput Batch

```python
import time
texts = [f"Texto {i}" for i in range(16)]
start = time.time()
r = requests.post("http://localhost:8000/translate", json={"text": texts})
elapsed = time.time() - start
print(f"Throughput: {len(texts)/elapsed:.1f} textos/segundo")
```

**Esperado**:
- [ ] Throughput: 8-15 textos/segundo (modelo 600M)

---

## 🔍 Verificación de Seguridad

### 20. Logs y Monitoreo

- [ ] Logs no contienen información sensible
- [ ] Logs muestran requests procesadas correctamente
- [ ] No hay errores repetidos en logs

### 21. Privacidad

- [ ] No hay llamadas a URLs externas (después del setup)
- [ ] Datos no se envían a servidores externos
- [ ] Todo el procesamiento es local

---

## 📝 Documentación

### 22. Archivos de Documentación

- [ ] `README.md` completo y claro
- [ ] `QUICKSTART.md` fácil de seguir
- [ ] `START_HERE.md` es el punto de entrada
- [ ] `PROJECT_SUMMARY.md` describe bien el proyecto
- [ ] Ejemplos en `examples/` funcionan

### 23. Código Documentado

- [ ] Funciones tienen docstrings
- [ ] Código tiene comentarios donde necesario
- [ ] Schemas tienen descripciones
- [ ] Variables de entorno documentadas

---

## ✅ Checklist Final

### Antes de Compartir/Desplegar

- [ ] Todos los tests pasan
- [ ] No hay errores de linting críticos
- [ ] Documentación está actualizada
- [ ] `.gitignore` excluye modelos y venv
- [ ] `requirements.txt` está completo
- [ ] `README.md` tiene instrucciones claras
- [ ] Ejemplos funcionan correctamente

### Producción (Si aplica)

- [ ] Variables de entorno en `.env` (no en código)
- [ ] Logs configurados apropiadamente
- [ ] Health checks funcionando
- [ ] Puerto configurado correctamente
- [ ] Volúmenes Docker montados
- [ ] Recursos (RAM/CPU) adecuados

---

## 🎉 ¡Listo para Usar!

Si todos los checkboxes están marcados, el proyecto está:

✅ **Instalado correctamente**  
✅ **Funcionando sin errores**  
✅ **Probado y verificado**  
✅ **Documentado completamente**  
✅ **Listo para producción**

---

## 🆘 Si Algo No Funciona

1. Ejecuta `make info` para ver el estado
2. Ejecuta `python scripts/check_system.py` para diagnosticar
3. Revisa los logs del servidor
4. Consulta la sección "Troubleshooting" en `README.md`
5. Verifica que todos los archivos del proyecto existan

---

**Última actualización**: 16 de Octubre, 2025  
**Versión**: 1.0.0

