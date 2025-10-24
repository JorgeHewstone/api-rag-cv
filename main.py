import os
from fastapi import FastAPI, Depends, HTTPException, Header, status
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import ollama
import lancedb
from langchain_ollama.embeddings import OllamaEmbeddings
from typing import AsyncGenerator

# --- Configuración ---
app = FastAPI()

# 1. (NUEVO) Configuración de CORS
# Esto le da permiso a tu sitio en Vercel para llamar a esta API.
origins = [
    "http://localhost:3000",  # Para tus pruebas locales
    # "https://tu-sitio-en-vercel.vercel.app", # ¡Añade tu URL de Vercel aquí!
    "*" # Por ahora, permite todo
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# # 2. (NUEVO) Configuración de Seguridad
# # Obtenemos la clave API secreta desde las variables de entorno de RunPod
# # Esta debe ser la MISMA clave que pones en .env.local de Vercel
# API_KEY_SECRET = os.environ.get("RUNPOD_API_KEY")

# if not API_KEY_SECRET:
#     print("ADVERTENCIA: No se ha configurado RUNPOD_API_KEY. La API no será segura.")

# # Función de dependencia para verificar la clave
# async def verify_api_key(authorization: str = Header(...)):
#     if not API_KEY_SECRET: # Permite el acceso si la clave no está configurada
#         return
        
#     if authorization != f"Bearer {API_KEY_SECRET}":
#         raise HTTPException(
#             status_code=status.HTTP_403_FORBIDDEN, 
#             detail="Authorization header inválido o ausente."
#         )

# --- Constantes del Modelo ---
DB_PATH = "./vectorstore"
MODELO_EMBEDDINGS = "nomic-embed-text"
MODELO_LLM = "phi3:mini"

# --- Tu System Prompt Personalizado ---
SYSTEM_PROMPT = """
Eres un asistente de IA profesional que representa a [Tu Nombre]. Tu propósito es responder preguntas sobre [Tu Nombre] a potenciales reclutadores y contactos de negocio.
Tu base de conocimientos es la información proporcionada en el CONTEXTO.
REGLAS ESTRICTAS:
1. Responde únicamente basándote en el CONTEXTO. No inventes información.
2. Si la pregunta es sobre [Tu Nombre] y el CONTEXTO tiene la respuesta, respóndela como un profesional de RRHH.
3. REGLA DE REDIRECCIÓN: Si la pregunta busca una debilidad (ej. "qué no sabes", "no tienes experiencia en X"), NUNCA digas "No sé" o "No tengo experiencia". En su lugar, reformula la respuesta de forma políticamente correcta, enfocándote en sus fortalezas adyacentes o en su gran facilidad para aprender.
    - Ejemplo Malo: "No, él no tiene experiencia en JavaScript."
    - Ejemplo Bueno: "Su fortaleza principal está en Python y el backend, pero aprende nuevas tecnologías rápidamente cuando un proyecto lo requiere."
4. REGLA DE CONTACTO: Si la información solicitada no está en el CONTEXTO, no inventes. Invita amablemente a la persona a contactar a [Tu Nombre] directamente.
    - Ejemplo: "Esa es una excelente pregunta. No tengo ese detalle específico, pero te invito a contactar a [Tu Nombre] directamente a [tu-email@dominio.com] para discutirlo."
"""

# --- Inicialización (Cargar Vector Store) ---
try:
    db = lancedb.connect(DB_PATH)
    table = db.open_table("info_personal")
    embeddings = OllamaEmbeddings(model=MODELO_EMBEDDINGS)
    print("Vector store cargado exitosamente.")
except Exception as e:
    print(f"Error al cargar el vector store: {e}")
    table = None

# --- Modelo de Petición ---
class ChatRequest(BaseModel):
    query: str
    
# --- Lógica de Streaming ---
async def stream_rag_response(query: str) -> AsyncGenerator[str, None]:
    if not table:
        yield "Error: La base de conocimientos (vector store) no está disponible."
        return

    # 1. Buscar en RAG
    embedded_query = embeddings.embed_query(query)
    results = table.search(embedded_query).limit(3).to_list()
    context = "\n".join([item['text'] for item in results])

    # 2. Construir el prompt para Ollama
    prompt_con_contexto = f"CONTEXTO:\n{context}\n\nPREGUNTA: {query}"
    
    # 3. Llamar a Ollama en modo streaming
    try:
        stream = ollama.chat(
            model=MODELO_LLM,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt_con_contexto},
            ],
            stream=True
        )

        # 4. Devolver cada chunk a medida que llega
        for chunk in stream:
            if 'content' in chunk['message']:
                yield chunk['message']['content']
                
    except Exception as e:
        yield f"Error al comunicarse con el modelo de IA: {e}"

# --- Endpoint de la API ---
# 3. (NUEVO) Añadimos la dependencia de seguridad
@app.post("/stream-ask")
async def ask_question(request: ChatRequest):
    return StreamingResponse(
        stream_rag_response(request.query), 
        media_type="text/event-stream"
    )

@app.get("/") # Endpoint de salud
def health_check():
    return {"status": "ok", "vector_store_loaded": table is not None}