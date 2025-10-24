# 1. Base de Python
FROM python:3.11-slim

# 2. Instalar curl (para bajar Ollama) y git
RUN apt-get update && apt-get install -y curl git && rm -rf /var/lib/apt/lists/*

# 3. Instalar Ollama
RUN curl -L https://ollama.com/download/ollama-linux-amd64 -o /usr/bin/ollama && \
    chmod +x /usr/bin/ollama

# 4. Establecer directorio de trabajo
WORKDIR /app

# 5. Instalar dependencias de Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 6. Copiar todo el código de la API
COPY . .

# 7. Ejecutar el script para construir el Vector Store
# Primero iniciamos Ollama en segundo plano y le damos tiempo
# Luego pre-descargamos los modelos y construimos el RAG
RUN (ollama serve & \
     sleep 10 && \
     ollama pull ${MODELO_EMBEDDINGS:-nomic-embed-text} && \
     ollama pull ${MODELO_LLM:-llama3.1:8b} && \
     python rag_builder.py \
    ) || (cat /root/.ollama/logs/server.log && exit 1)

# 8. Exponer el puerto
EXPOSE 8080

# 9. Script de inicio
COPY start.sh .
RUN chmod +x start.sh
CMD ["./start.sh"]