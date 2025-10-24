# 1. Base de Python
FROM python:3.11

# 2. Instalar dependencias del sistema (curl, git, bash)
RUN apt-get update && apt-get install -y curl git bash && rm -rf /var/lib/apt/lists/*

# 3. (CORREGIDO) Instalar Ollama usando el script oficial
RUN curl -fSL https://ollama.com/install.sh | sh

# 4. Establecer directorio de trabajo
WORKDIR /app

# 5. Instalar dependencias de Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 6. Copiar todo el código de la API
COPY . .

# 7. Dar permisos a los scripts
COPY build.sh .
COPY start.sh .
RUN chmod +x build.sh
RUN chmod +x start.sh

# 8. Ejecutar el script de build (no cambia)
RUN bash ./build.sh

# 9. Exponer el puerto (no cambia)
EXPOSE 8080

# 10. Script de inicio (no cambia)
CMD ["bash", "./start.sh"]