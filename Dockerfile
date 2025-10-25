# 1. Base de Python
FROM python:3.11

# 2. Instalar dependencias del sistema (curl, git, bash)
RUN apt-get update && apt-get install -y curl git bash && rm -rf /var/lib/apt/lists/*

# 3. Instalar Ollama usando el script oficial
RUN curl -fSL https://ollama.com/install.sh | sh

# 4. Establecer directorio de trabajo
WORKDIR /app

# 5. Instalar dependencias de Python (AHORA INCLUYE runpod)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 6. Copiar todo el código de la API
COPY . .

# 7. Dar permisos a los scripts
COPY build.sh .
RUN chmod +x build.sh

# 8. Ejecutar el script de build (para crear el RAG)
RUN bash ./build.sh

# 9. Exponer el puerto (RunPod lo ignora, pero es buena práctica)
EXPOSE 8080

# 10. (CORREGIDO) Comando de inicio: EJECUTAR main.py
# Ya no usamos start.sh ni uvicorn. runpod.serverless.start() maneja el servidor.
# Necesitamos iniciar ollama serve en segundo plano ANTES de iniciar el handler.
CMD bash -c "ollama serve & python main.py"