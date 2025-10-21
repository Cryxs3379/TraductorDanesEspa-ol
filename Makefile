# Makefile para proyecto de traducción ES → DA con NLLB + CTranslate2
#
# Comandos principales:
#   make venv      - Crear entorno virtual e instalar dependencias
#   make download  - Descargar modelo desde HuggingFace
#   make convert   - Convertir modelo a CTranslate2 INT8
#   make run       - Ejecutar servidor FastAPI
#   make test      - Ejecutar tests
#   make docker-build - Construir imagen Docker
#   make docker-run   - Ejecutar contenedor Docker

# Variables de configuración (pueden sobreescribirse con .env)
-include .env
export

PYTHON := python3
VENV := venv
VENV_BIN := $(VENV)/bin
PIP := $(VENV_BIN)/pip
PYTHON_VENV := $(VENV_BIN)/python

# Configuración de modelo por defecto
MODEL_NAME ?= facebook/nllb-200-distilled-600M
MODEL_DIR ?= ./models/nllb-600m
CT2_DIR ?= ./models/nllb-600m-ct2-int8

# Configuración Docker
DOCKER_IMAGE := traductor-es-da
DOCKER_TAG := latest
DOCKER_MODELS_DIR := ./models

.PHONY: help
help: ## Mostrar ayuda
	@echo "======================================================================"
	@echo "Traductor Español → Danés (NLLB + CTranslate2)"
	@echo "======================================================================"
	@echo ""
	@echo "Comandos disponibles:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'
	@echo ""
	@echo "Flujo de trabajo típico:"
	@echo "  1. make venv          # Crear entorno virtual"
	@echo "  2. make download      # Descargar modelo (600M por defecto)"
	@echo "  3. make convert       # Convertir a CT2 INT8"
	@echo "  4. make run           # Ejecutar servidor"
	@echo ""
	@echo "Con Docker:"
	@echo "  1. make download      # Descargar modelo en host"
	@echo "  2. make convert       # Convertir en host"
	@echo "  3. make docker-build  # Construir imagen"
	@echo "  4. make docker-run    # Ejecutar contenedor"
	@echo "======================================================================"

.PHONY: venv
venv: ## Crear entorno virtual e instalar dependencias
	@echo "Creando entorno virtual..."
	$(PYTHON) -m venv $(VENV)
	@echo "Actualizando pip..."
	$(PIP) install --upgrade pip setuptools wheel
	@echo "Instalando dependencias..."
	$(PIP) install -r requirements.txt
	@echo "✓ Entorno virtual creado en ./$(VENV)"
	@echo ""
	@echo "Activa el entorno con:"
	@echo "  source $(VENV_BIN)/activate  # Linux/Mac"
	@echo "  $(VENV)\\Scripts\\activate     # Windows"

.PHONY: install
install: venv ## Alias para venv

.PHONY: download
download: ## Descargar modelo desde HuggingFace
	@echo "Descargando modelo: $(MODEL_NAME)"
	@echo "Destino: $(MODEL_DIR)"
	@if [ -d "$(VENV)" ]; then \
		$(PYTHON_VENV) scripts/download_model.py --model $(MODEL_NAME) --out $(MODEL_DIR); \
	else \
		$(PYTHON) scripts/download_model.py --model $(MODEL_NAME) --out $(MODEL_DIR); \
	fi

.PHONY: download-1.3b
download-1.3b: ## Descargar modelo 1.3B (requiere más RAM)
	@$(MAKE) download MODEL_NAME=facebook/nllb-200-1.3B MODEL_DIR=./models/nllb-1.3b

.PHONY: convert
convert: ## Convertir modelo a CTranslate2 INT8
	@echo "Convirtiendo modelo a CTranslate2 INT8"
	@echo "Entrada: $(MODEL_DIR)"
	@echo "Salida: $(CT2_DIR)"
	@bash scripts/convert_to_ct2.sh --in $(MODEL_DIR) --out $(CT2_DIR)

.PHONY: run
run: ## Ejecutar servidor FastAPI local (con auto-detección de puerto)
	@echo "Iniciando servidor FastAPI..."
	@if [ -d "$(VENV)" ]; then \
		$(PYTHON_VENV) start_server.py; \
	else \
		$(PYTHON) start_server.py; \
	fi

.PHONY: test
test: ## Ejecutar tests con pytest
	@echo "Ejecutando tests..."
	@if [ -d "$(VENV)" ]; then \
		$(VENV_BIN)/pytest tests/ -v --tb=short; \
	else \
		pytest tests/ -v --tb=short; \
	fi

.PHONY: test-verbose
test-verbose: ## Ejecutar tests con output detallado
	@if [ -d "$(VENV)" ]; then \
		$(VENV_BIN)/pytest tests/ -v -s; \
	else \
		pytest tests/ -v -s; \
	fi

.PHONY: test-cov
test-cov: ## Ejecutar tests con coverage
	@echo "Ejecutando tests con coverage..."
	@if [ -d "$(VENV)" ]; then \
		$(VENV_BIN)/pytest tests/ --cov=app --cov-report=html --cov-report=term; \
	else \
		pytest tests/ --cov=app --cov-report=html --cov-report=term; \
	fi

.PHONY: lint
lint: ## Ejecutar linters (ruff)
	@echo "Ejecutando linter..."
	@if [ -d "$(VENV)" ]; then \
		$(VENV_BIN)/ruff check app/ tests/; \
	else \
		ruff check app/ tests/; \
	fi

.PHONY: lint-fix
lint-fix: ## Corregir problemas de linting automáticamente
	@echo "Corrigiendo problemas de linting..."
	@if [ -d "$(VENV)" ]; then \
		$(VENV_BIN)/ruff check --fix app/ tests/; \
	else \
		ruff check --fix app/ tests/; \
	fi

.PHONY: format
format: ## Formatear código con black e isort
	@echo "Formateando código..."
	@if [ -d "$(VENV)" ]; then \
		$(VENV_BIN)/black app/ tests/; \
		$(VENV_BIN)/isort app/ tests/; \
	else \
		black app/ tests/; \
		isort app/ tests/; \
	fi

.PHONY: typecheck
typecheck: ## Ejecutar type checking con mypy
	@echo "Ejecutando type checking..."
	@if [ -d "$(VENV)" ]; then \
		$(VENV_BIN)/mypy app/; \
	else \
		mypy app/; \
	fi

.PHONY: security
security: ## Ejecutar auditoría de seguridad
	@echo "Ejecutando auditoría de seguridad..."
	@if [ -d "$(VENV)" ]; then \
		$(VENV_BIN)/bandit -r app/ -f json -o bandit-report.json || true; \
		$(VENV_BIN)/safety check --json || true; \
	else \
		bandit -r app/ -f json -o bandit-report.json || true; \
		safety check --json || true; \
	fi

.PHONY: quality
quality: lint typecheck test ## Ejecutar todas las verificaciones de calidad
	@echo "✓ Todas las verificaciones de calidad completadas"

.PHONY: clean
clean: ## Limpiar archivos temporales
	@echo "Limpiando archivos temporales..."
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	@echo "✓ Limpieza completada"

.PHONY: clean-all
clean-all: clean ## Limpiar todo incluyendo venv y modelos
	@echo "¿Estás seguro de eliminar venv y modelos? [y/N] " && read ans && [ $${ans:-N} = y ]
	rm -rf $(VENV)
	rm -rf models/
	@echo "✓ Todo limpiado (venv y modelos eliminados)"

.PHONY: build
build: quality ## Construir aplicación (backend + frontend) después de verificar calidad
	@echo "Construyendo aplicación..."
	cd frontend && npm run build
	@echo "✓ Build completado"

.PHONY: e2e
e2e: ## Ejecutar tests end-to-end
	@echo "Ejecutando tests E2E..."
	@if [ -d "$(VENV)" ]; then \
		$(VENV_BIN)/pytest tests/ -m integration -v; \
	else \
		pytest tests/ -m integration -v; \
	fi

.PHONY: docker-build
docker-build: ## Construir imagen Docker
	@echo "Construyendo imagen Docker..."
	docker build -t $(DOCKER_IMAGE):$(DOCKER_TAG) .
	@echo "✓ Imagen construida: $(DOCKER_IMAGE):$(DOCKER_TAG)"

.PHONY: docker-run
docker-run: ## Ejecutar contenedor Docker (monta ./models como volumen)
	@echo "Ejecutando contenedor Docker..."
	@echo "IMPORTANTE: Asegúrate de haber descargado y convertido el modelo primero"
	@echo ""
	docker run -d \
		--name traductor-es-da \
		-p 8000:8000 \
		-v $(PWD)/models:/models:ro \
		-e MODEL_DIR=/models/nllb-600m \
		-e CT2_DIR=/models/nllb-600m-ct2-int8 \
		$(DOCKER_IMAGE):$(DOCKER_TAG)
	@echo ""
	@echo "✓ Contenedor iniciado"
	@echo "  Accede a: http://localhost:8000"
	@echo "  Logs: docker logs -f traductor-es-da"
	@echo "  Detener: docker stop traductor-es-da"
	@echo "  Eliminar: docker rm traductor-es-da"

.PHONY: docker-stop
docker-stop: ## Detener contenedor Docker
	docker stop traductor-es-da
	docker rm traductor-es-da

.PHONY: docker-logs
docker-logs: ## Ver logs del contenedor Docker
	docker logs -f traductor-es-da

.PHONY: docker-shell
docker-shell: ## Abrir shell en el contenedor Docker
	docker exec -it traductor-es-da /bin/bash

.PHONY: curl-test
curl-test: ## Test rápido con curl
	@echo "Testeando endpoint /translate..."
	@curl -X POST http://localhost:8000/translate \
		-H "Content-Type: application/json" \
		-d '{"text": "Hola mundo", "max_new_tokens": 128}' \
		| python -m json.tool

.PHONY: preflight
preflight: ## Ejecutar verificación de entorno (preflight check)
	@echo "Ejecutando preflight check..."
	@if [ -d "$(VENV)" ]; then \
		$(PYTHON_VENV) scripts/preflight.py; \
	else \
		$(PYTHON) scripts/preflight.py; \
	fi

.PHONY: info
info: preflight ## Mostrar configuración actual y estado del sistema

.DEFAULT_GOAL := help

