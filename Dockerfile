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

# 7. (NUEVO) Dar permisos al script de build y al de start
COPY build.sh .
COPY start.sh .
RUN chmod +x build.sh
RUN chmod +x start.sh

# 8. (NUEVO) Ejecutar el script de build (el que acabamos de crear)
RUN ./build.sh

# 9. Exponer el puerto
EXPOSE 8080

# 10. Script de inicio (este comando no cambia)
CMD ["./start.sh"]