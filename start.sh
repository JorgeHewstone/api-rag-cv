#!/bin/sh

# 1. Inicia el servidor de Ollama en segundo plano
ollama serve &

# 2. Espera unos segundos a que esté listo
sleep 5

# 3. Inicia la API de FastAPI en primer plano
uvicorn main:app --host 0.0.0.0 --port 8080