from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse # Aunque no lo usemos ahora
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
# Comenta imports de ollama, lancedb, langchain

app = FastAPI()
origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    query: str

@app.post("/stream-ask")
async def ask_question_test(request: Request, chat_request: ChatRequest):
    print(f">>> DEBUG: Petición de prueba recibida en /stream-ask. Query: {chat_request.query}")
    async def dummy_stream(): # Stream falso para que la respuesta sea válida
        yield f"Recibido: {chat_request.query}"
    return StreamingResponse(dummy_stream(), media_type="text/event-stream")

@app.get("/")
def health_check():
    return {"status": "ok_test"}

print(">>> DEBUG: Aplicación FastAPI de prueba iniciada.")










# import os
# from fastapi import FastAPI, Request # Importa Request para obtener headers
# from fastapi.responses import StreamingResponse
# from fastapi.middleware.cors import CORSMiddleware
# from pydantic import BaseModel
# import ollama
# import lancedb
# from langchain_ollama.embeddings import OllamaEmbeddings
# from typing import AsyncGenerator

# # --- Configuración ---
# app = FastAPI()

# # Configuración de CORS (sin cambios)
# origins = [
#     "http://localhost:3000",
#     "*"
# ]
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=origins,
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# # --- Constantes del Modelo ---
# DB_PATH = "./vectorstore"
# MODELO_EMBEDDINGS = "nomic-embed-text"
# MODELO_LLM = "phi3:mini" 

# # --- System Prompt (sin cambios) ---
# SYSTEM_PROMPT = """
# Eres un asistente de IA profesional que representa a Jorge Hewstone. Tu deber es que la persona que interactua contigo se convenza
# de que Jorge Hewstone es un gran Machine learning engineer. 
# Tendrás acceso a su información para poder responder las preguntas con precisión (no inventes nada concreto).
# Si sientes que la información no responde alguna pregunta que pueda poner en duda las capacidades de Jorge, puedes usar
# la información que ya está para argumentar que Jorge podría mejorar y aprender muy rápido.
# """

# # --- Inicialización (Cargar Vector Store) ---
# print(">>> DEBUG: Cargando Vector Store...") # Print 1: Inicio de carga
# try:
#     db = lancedb.connect(DB_PATH)
#     table = db.open_table("info_personal")
#     embeddings = OllamaEmbeddings(model=MODELO_EMBEDDINGS)
#     print(">>> DEBUG: Vector store cargado exitosamente.") # Print 2: Carga exitosa
# except Exception as e:
#     print(f">>> DEBUG: ERROR al cargar el vector store: {e}") # Print 3: Error de carga
#     table = None

# # --- Modelo de Petición (sin cambios) ---
# class ChatRequest(BaseModel):
#     query: str

# # --- Lógica de Streaming ---
# async def stream_rag_response(query: str) -> AsyncGenerator[str, None]:
#     print(f">>> DEBUG: Iniciando stream_rag_response con query: '{query}'") # Print 5: Entra a la lógica principal
#     if not table:
#         print(">>> DEBUG: Error - Vector store no disponible.") # Print 6: Error si no hay RAG
#         yield "Error: La base de conocimientos (vector store) no está disponible."
#         return

#     try:
#         # 1. Buscar en RAG
#         print(">>> DEBUG: Generando embedding para la query...") # Print 7: Antes del embedding
#         embedded_query = embeddings.embed_query(query)
#         print(">>> DEBUG: Embedding generado. Buscando en LanceDB...") # Print 8: Antes de buscar
#         results = table.search(embedded_query).limit(3).to_list()
#         context = "\n".join([item['text'] for item in results])
#         print(f">>> DEBUG: Contexto encontrado: {context[:100]}...") # Print 9: Muestra parte del contexto

#         # 2. Construir el prompt para Ollama
#         prompt_con_contexto = f"CONTEXTO:\n{context}\n\nPREGUNTA: {query}"
#         print(f">>> DEBUG: Prompt final para Ollama: {prompt_con_contexto[:100]}...") # Print 10: Muestra parte del prompt

#         # 3. Llamar a Ollama en modo streaming
#         print(f">>> DEBUG: Llamando a ollama.chat con modelo {MODELO_LLM}...") # Print 11: Antes de llamar a Ollama
#         stream = ollama.chat(
#             model=MODELO_LLM,
#             messages=[
#                 {"role": "system", "content": SYSTEM_PROMPT},
#                 {"role": "user", "content": prompt_con_contexto},
#             ],
#             stream=True
#         )

#         # 4. Devolver cada chunk a medida que llega
#         print(">>> DEBUG: Recibiendo stream de Ollama...") # Print 12: Empieza el stream
#         chunk_count = 0
#         for chunk in stream:
#             if 'content' in chunk['message']:
#                 # print(f">>> DEBUG: Yield chunk {chunk_count}") # Descomenta si quieres ver CADA chunk
#                 yield chunk['message']['content']
#                 chunk_count += 1
#         print(f">>> DEBUG: Stream de Ollama finalizado. Total chunks: {chunk_count}") # Print 13: Termina el stream

#     except Exception as e:
#         print(f">>> DEBUG: ERROR dentro de stream_rag_response: {e}") # Print 14: Captura error interno
#         yield f"Error durante el procesamiento de la IA: {e}"

# # --- Endpoint de la API ---
# # Quitamos la seguridad duplicada
# @app.post("/stream-ask")
# async def ask_question(request: Request, chat_request: ChatRequest): # Modificado para recibir Request y ChatRequest
#     # Imprime headers para depuración de CORS o Auth si fuera necesario
#     print(f">>> DEBUG: Petición recibida en /stream-ask. Headers: {dict(request.headers)}") # Print 4: Petición recibida
    
#     # Validar que el cuerpo (body) se parseó correctamente
#     if not chat_request or not chat_request.query:
#          print(">>> DEBUG: Error - Cuerpo de la petición inválido o 'query' ausente.")
#          # Puedes devolver un error más específico si quieres
#          # raise HTTPException(status_code=400, detail="Cuerpo de la petición inválido.")
#          # Por ahora, dejamos que falle y lo veremos en los logs
    
#     # Llama a la lógica de streaming usando el query del cuerpo parseado
#     return StreamingResponse(
#         stream_rag_response(chat_request.query),
#         media_type="text/event-stream"
#     )

# @app.get("/") # Endpoint de salud (sin cambios)
# def health_check():
#     return {"status": "ok", "vector_store_loaded": table is not None}

# print(">>> DEBUG: Aplicación FastAPI iniciada.") # Print de inicio general