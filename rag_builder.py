import lancedb
from langchain_community.document_loaders import TextLoader
from langchain_community.vectorstores import LanceDB
from langchain_ollama.embeddings import OllamaEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

DB_PATH = "./vectorstore"
MODELO_EMBEDDINGS = "nomic-embed-text" # Un modelo de embeddings rápido y ligero

def build_vectorstore():
    print("Iniciando la creación del vector store...")
    
    # 1. Cargar el documento de texto
    loader = TextLoader("info.txt", encoding="utf-8")
    documents = loader.load()

    # 2. Dividir el texto en pedazos (chunks)
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    docs = text_splitter.split_documents(documents)

    # 3. Inicializar el modelo de embeddings (usando Ollama)
    print(f"Usando el modelo de embeddings: {MODELO_EMBEDDINGS}")
    embeddings = OllamaEmbeddings(model=MODELO_EMBEDDINGS)

    # 4. Conectar a LanceDB y crear la base de datos
    db = lancedb.connect(DB_PATH)
    table = db.create_table(
        "info_personal",
        data=[
            {
                "vector": embeddings.embed_query(doc.page_content),
                "text": doc.page_content,
                "source": doc.metadata.get("source", "info.txt"),
            }
            for doc in docs
        ],
        mode="overwrite",
    )
    
    print(f"¡Vector store creado exitosamente en {DB_PATH} con {len(docs)} chunks!")

if __name__ == "__main__":
    # El Dockerfile ya se ha encargado de iniciar 'ollama serve'
    # y de hacer 'pull' del modelo de embeddings.
    # Por lo tanto, solo necesitamos ejecutar la función.
    try:
        build_vectorstore()
    except Exception as e:
        print(f"Error al construir el vector store: {e}")
        # Es útil imprimir los logs de Ollama si falla
        print("--- Intentando leer logs de Ollama ---")
        try:
            with open("/root/.ollama/logs/server.log", "r") as f:
                print(f.read())
        except:
            print("No se pudieron leer los logs de Ollama.")
        exit(1) # Falla el build de Docker si esto no funciona