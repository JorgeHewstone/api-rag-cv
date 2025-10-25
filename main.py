print("--- SCRIPT main.py INICIADO ---") # Log inicial
import runpod
import ollama
import lancedb
from langchain_ollama.embeddings import OllamaEmbeddings
from pydantic import BaseModel, ValidationError
from typing import AsyncGenerator
import asyncio
import subprocess # <-- Importar subprocess
import time # <-- Importar time
import sys # <-- Importar sys para ver la salida

# --- Configuración y Carga de RAG (igual que antes) ---
DB_PATH = "./vectorstore"
MODELO_EMBEDDINGS = "nomic-embed-text"
MODELO_LLM = "phi3:mini"
SYSTEM_PROMPT = """
Eres un asistente de IA profesional que representa a Jorge Hewstone. Tu deber es que la persona que interactua contigo se convenza
de que Jorge Hewstone es un gran Machine learning engineer. 
Tendrás acceso a su información para poder responder las preguntas con precisión (no inventes nada concreto).
Si sientes que la información no responde alguna pregunta que pueda poner en duda las capacidades de Jorge, puedes usar
la información que ya está para argumentar que Jorge podría mejorar y aprender muy rápido.
"""
print(">>> DEBUG: Cargando Vector Store...")
try:
    db = lancedb.connect(DB_PATH)
    table = db.open_table("info_personal")
    embeddings = OllamaEmbeddings(model=MODELO_EMBEDDINGS)
    print(">>> DEBUG: Vector store cargado exitosamente.")
except Exception as e:
    print(f">>> DEBUG: ERROR al cargar el vector store: {e}")
    table = None

# --- Modelo de Petición ---
class ChatRequest(BaseModel):
    query: str

# --- Lógica de Streaming (igual que antes, con AsyncClient) ---
async def stream_rag_response(query: str) -> AsyncGenerator[str, None]:
    print(f">>> DEBUG: Iniciando stream_rag_response con query: '{query}'")
    if not table:
        print(">>> DEBUG: Error - Vector store no disponible.")
        yield "Error: La base de conocimientos (vector store) no está disponible."
        return
    try:
        # ... (Lógica RAG igual) ...
        print(">>> DEBUG: Generando embedding...")
        embedded_query = embeddings.embed_query(query)
        print(">>> DEBUG: Buscando en LanceDB...")
        results = table.search(embedded_query).limit(3).to_list()
        context = "\n".join([item['text'] for item in results])
        prompt_con_contexto = f"CONTEXTO:\n{context}\n\nPREGUNTA: {query}"
        print(f">>> DEBUG: Llamando a ollama.chat con modelo {MODELO_LLM}...")
        
        # Usamos AsyncClient
        stream = await ollama.AsyncClient().chat(
            model=MODELO_LLM,
            messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt_con_contexto},
            ],
            stream=True
        )
        print(">>> DEBUG: Recibiendo stream de Ollama...")
        chunk_count = 0
        async for chunk in stream:
             if 'message' in chunk and 'content' in chunk['message']:
                yield chunk['message']['content']
                chunk_count += 1
        print(f">>> DEBUG: Stream de Ollama finalizado. Total chunks: {chunk_count}")

    except Exception as e:
        print(f">>> DEBUG: ERROR dentro de stream_rag_response: {e}")
        yield f"Error durante el procesamiento de la IA: {e}"

# --- EL HANDLER HTTP DE RUNPOD (igual que antes) ---
async def handler_http(job):
    print(f">>> DEBUG: Job HTTP recibido: {job}")
    job_input = job.get('input', None)
    # ... (Validación Pydantic igual) ...
    try:
        chat_request = ChatRequest(**job_input)
        print(f">>> DEBUG: Input validado: query='{chat_request.query}'")
    except ValidationError as e:
        print(f">>> DEBUG: Error de validación de input: {e}")
        return {"error": f"Input inválido: {e}"}

    return {"output": stream_rag_response(chat_request.query)}

# --- Iniciar Ollama y luego el Worker de RunPod ---
def start_ollama():
    print(">>> DEBUG: Intentando iniciar 'ollama serve' en segundo plano...")
    # Redirigir stdout y stderr a archivos para depuración si es necesario
    try:
        # Usamos Popen para no bloquear
        process = subprocess.Popen(["ollama", "serve"], stdout=sys.stdout, stderr=sys.stderr) 
        print(f">>> DEBUG: Proceso 'ollama serve' iniciado con PID: {process.pid}")
        # Espera corta para darle tiempo a iniciar
        time.sleep(5) 
        # Podríamos añadir un bucle de chequeo aquí si 5s no es suficiente
        return process
    except FileNotFoundError:
        print(">>> DEBUG: ERROR - El comando 'ollama' no se encontró. ¿Está instalado?")
        return None
    except Exception as e:
        print(f">>> DEBUG: ERROR al iniciar 'ollama serve': {e}")
        return None

if __name__ == "__main__":
    ollama_process = start_ollama()
    if ollama_process:
        print(">>> DEBUG: Ollama iniciado. Asegurando modelos...")
        # Aseguramos que los modelos estén disponibles al inicio
        try:
            # Usamos el cliente síncrono aquí porque es más simple al inicio
            ollama.pull(MODELO_EMBEDDINGS)
            ollama.pull(MODELO_LLM)
            print(">>> DEBUG: Modelos Ollama verificados/descargados.")
        except Exception as e:
            print(f">>> DEBUG: ERROR al hacer pull de modelos Ollama: {e}")
            # Considera si quieres detenerte aquí si los modelos fallan

        print(">>> DEBUG: Iniciando worker HTTP de RunPod...")
        runpod.serverless.start({
            "handler": handler_http,
            "return_async": True
        })
    else:
        print(">>> DEBUG: No se pudo iniciar Ollama. El worker de RunPod no se iniciará.")

# Nota: No necesitamos iniciar 'ollama serve' para esta prueba mínima.
# Lo quitaremos temporalmente del Dockerfile también.

# import runpod
# import ollama
# import lancedb
# from langchain_ollama.embeddings import OllamaEmbeddings
# from pydantic import BaseModel, ValidationError
# from typing import AsyncGenerator

# # --- Configuración (Movida al inicio global) ---
# DB_PATH = "./vectorstore"
# MODELO_EMBEDDINGS = "nomic-embed-text"
# MODELO_LLM = "phi3:mini"
# print(">>> DEBUG: Configuración cargada.")

# # --- System Prompt (sin cambios) ---
# SYSTEM_PROMPT = """
# Eres un asistente de IA profesional que representa a Jorge Hewstone. Tu deber es que la persona que interactua contigo se convenza
# de que Jorge Hewstone es un gran Machine learning engineer. 
# Tendrás acceso a su información para poder responder las preguntas con precisión (no inventes nada concreto).
# Si sientes que la información no responde alguna pregunta que pueda poner en duda las capacidades de Jorge, puedes usar
# la información que ya está para argumentar que Jorge podría mejorar y aprender muy rápido.
# """
# print(">>> DEBUG: System prompt definido.")

# # --- Inicialización (Cargar Vector Store - Global) ---
# print(">>> DEBUG: Cargando Vector Store...")
# try:
#     db = lancedb.connect(DB_PATH)
#     table = db.open_table("info_personal")
#     embeddings = OllamaEmbeddings(model=MODELO_EMBEDDINGS)
#     print(">>> DEBUG: Vector store cargado exitosamente.")
# except Exception as e:
#     print(f">>> DEBUG: ERROR al cargar el vector store: {e}")
#     table = None

# # --- Modelo de Petición (Usando Pydantic) ---
# class ChatRequest(BaseModel):
#     query: str
# print(">>> DEBUG: Modelo ChatRequest definido.")

# # --- Lógica de Streaming (Igual que antes) ---
# async def stream_rag_response(query: str) -> AsyncGenerator[dict, None]:
#     # RunPod espera que el stream devuelva diccionarios, no solo strings
#     print(f">>> DEBUG: Iniciando stream_rag_response con query: '{query}'")
#     if not table:
#         print(">>> DEBUG: Error - Vector store no disponible.")
#         yield {"output": "Error: La base de conocimientos (vector store) no está disponible.", "error": True}
#         return

#     try:
#         # 1. Buscar en RAG
#         print(">>> DEBUG: Generando embedding para la query...")
#         embedded_query = embeddings.embed_query(query)
#         print(">>> DEBUG: Embedding generado. Buscando en LanceDB...")
#         results = table.search(embedded_query).limit(3).to_list()
#         context = "\n".join([item['text'] for item in results])
#         print(f">>> DEBUG: Contexto encontrado: {context[:100]}...")

#         # 2. Construir el prompt para Ollama
#         prompt_con_contexto = f"CONTEXTO:\n{context}\n\nPREGUNTA: {query}"
#         print(f">>> DEBUG: Prompt final para Ollama: {prompt_con_contexto[:100]}...")

#         # 3. Llamar a Ollama en modo streaming
#         print(f">>> DEBUG: Llamando a ollama.chat con modelo {MODELO_LLM}...")
#         stream = ollama.chat(
#             model=MODELO_LLM,
#             messages=[
#                 {"role": "system", "content": SYSTEM_PROMPT},
#                 {"role": "user", "content": prompt_con_contexto},
#             ],
#             stream=True
#         )

#         # 4. Devolver cada chunk como un diccionario
#         print(">>> DEBUG: Recibiendo stream de Ollama...")
#         chunk_count = 0
#         async for chunk in stream: # Usamos async for para iterar el stream asíncrono
#             if 'message' in chunk and 'content' in chunk['message']:
#                 yield {"output": chunk['message']['content']} # Devolvemos diccionario
#                 chunk_count += 1
#         print(f">>> DEBUG: Stream de Ollama finalizado. Total chunks: {chunk_count}")

#     except Exception as e:
#         print(f">>> DEBUG: ERROR dentro de stream_rag_response: {e}")
#         yield {"output": f"Error durante el procesamiento de la IA: {e}", "error": True}


# # --- EL HANDLER DE RUNPOD ---
# async def handler(job):
#     """
#     Esta es la función que RunPod ejecutará para cada petición.
#     El input del job viene en job['input'].
#     """
#     print(f">>> DEBUG: Job recibido por el handler: {job}") # Print importante

#     job_input = job.get('input', None)
#     if job_input is None:
#         return {"error": "No se recibió 'input' en el job."}

#     # Validamos la entrada usando Pydantic
#     try:
#         chat_request = ChatRequest(**job_input)
#         print(f">>> DEBUG: Input validado: query='{chat_request.query}'")
#     except ValidationError as e:
#         print(f">>> DEBUG: Error de validación de input: {e}")
#         return {"error": f"Input inválido: {e}"}

#     # Retornamos el generador asíncrono directamente
#     # RunPod maneja generadores para streaming
#     return stream_rag_response(chat_request.query)

# # --- Iniciar el Worker de RunPod ---
# print(">>> DEBUG: Iniciando worker de RunPod...")
# runpod.serverless.start({"handler": handler})


