#!/bin/bash

# 1. Inicia el servidor de Ollama en segundo plano
ollama serve &

# 2. Espera unos segundos a que esté listo
sleep 5


# 3. Descargando modelos si no existiesen
# echo "Asegurando que los modelos Ollama estén descargados..."
# ollama pull ${MODELO_EMBEDDINGS:-nomic-embed-text}
# ollama pull ${MODELO_LLM:-phi3:mini}
# echo "Modelos listos."


# 3. Inicia la API de FastAPI en primer plano
uvicorn main:app --host 0.0.0.0 --port 8080