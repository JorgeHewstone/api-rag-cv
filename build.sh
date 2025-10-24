#!/bin/bash

# 1. MODO DEPURACIÓN: Imprime cada comando que se ejecuta
set -x

# 2. SANITY CHECK: Verifica que ollama esté instalado y dónde
echo "--- Verificando la instalación de Ollama ---"
which ollama
ollama --version

# 3. Inicia Ollama y REDIRIGE TODOS LOS LOGS a un archivo
echo "--- Iniciando Ollama en segundo plano... ---"
ollama serve > ollama.log 2>&1 &
OLLAMA_PID=$!

# 4. Bucle de espera (sin cambios, pero ahora veremos los logs de 'curl')
echo "--- Esperando a que Ollama responda... ---"
n=0
while [ $n -lt 45 ]; do
  # Usamos 'curl -s ... | grep ...' como una prueba de éxito
  if curl -s http://127.0.0.1:11434 | grep "Ollama is running"; then
    echo "Ollama está listo."
    break
  fi
  
  echo "Ollama no está listo. Esperando 1s..."
  sleep 1
  n=$((n+1))
done

# 5. Si falla, imprime los logs que capturamos
if [ $n -eq 45 ]; then
  echo "--- ERROR: Ollama no pudo iniciarse después de 45 segundos. ---"
  echo "--- Mostrando los logs de ollama.log ---"
  cat ollama.log
  exit 1
fi

# 6. Si todo va bien, continúa
echo "--- Descargando modelo de embeddings: ${MODELO_EMBEDDINGS:-nomic-embed-text} ---"
ollama pull ${MODELO_EMBEDDINGS:-nomic-embed-text}

# echo "--- Descargando modelo LLM: ${MODELO_LLM:-llama3.1:8b} ---"
# ollama pull ${MODELO_LLM:-phi3:mini}

echo "--- Ejecutando el script rag_builder.py... ---"
python rag_builder.py

# 7. Detiene el servidor
echo "--- Build de RAG completado. Deteniendo servidor Ollama temporal. ---"
kill $OLLAMA_PID

# Desactiva el modo de depuración al final
set +x