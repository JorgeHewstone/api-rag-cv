#!/bin/sh

# Inicia el servidor de Ollama en segundo plano
echo "Iniciando Ollama en segundo plano..."
ollama serve &

# Guarda el ID del proceso
OLLAMA_PID=$!

# Bucle de espera (más robusto que 'sleep')
# Espera hasta 45 segundos a que Ollama esté listo
echo "Esperando a que Ollama responda..."
n=0
while [ $n -lt 45 ]; do
  # Comprueba si el servidor responde
  status=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:11434)
  
  if [ $status -eq 200 ]; then
    echo "Ollama está listo."
    break
  fi
  
  echo "Ollama no está listo (Status: $status). Esperando 1s..."
  sleep 1
  n=$((n+1))
done

# Si el bucle termina sin éxito, falla el build
if [ $n -eq 45 ]; then
  echo "Error: Ollama no pudo iniciarse después de 45 segundos."
  echo "--- Logs de Ollama ---"
  cat /root/.ollama/logs/server.log
  exit 1
fi

# Si todo va bien, continúa con las descargas y el build del RAG
echo "Descargando modelo de embeddings: ${MODELO_EMBEDDINGS:-nomic-embed-text}"
ollama pull ${MODELO_EMBEDDINGS:-nomic-embed-text}

echo "Descargando modelo LLM: ${MODELO_LLM:-llama3.1:8b}"
ollama pull ${MODELO_LLM:-llama3.1:8b}

echo "Ejecutando el script rag_builder.py..."
python rag_builder.py

# Detiene el servidor de Ollama en segundo plano
echo "Build de RAG completado. Deteniendo servidor Ollama temporal."
kill $OLLAMA_PID