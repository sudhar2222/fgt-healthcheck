from langchain_community.document_loaders import DirectoryLoader, TextLoader, PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import Chroma
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.llms import Ollama
from langchain.chains import RetrievalQA
import os

# === 1. Load Documents ===
def load_documents(path="data"):
    docs = []
    for file in os.listdir(path):
        full_path = os.path.join(path, file)
        if file.endswith(".txt"):
            loader = TextLoader(full_path)
        elif file.endswith(".pdf"):
            loader = PyPDFLoader(full_path)
        else:
            print(f"Skipping unsupported file: {file}")
            continue
        docs.extend(loader.load())
    return docs


# === 2. Split into Chunks ===
def split_documents(docs):
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    return splitter.split_documents(docs)


# === 3. Create Local Embeddings + Vector Store ===
def create_vector_store(chunks):
    embedding = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    vectordb = Chroma.from_documents(chunks, embedding, persist_directory="db")
    vectordb.persist()
    return vectordb


# === 4. Connect Local Llama Model ===
def get_llm():
    # Works if you run Ollama locally:  ollama serve
    return Ollama(model="llama3.2:1b")


# === 5. Build the QA Chain ===
def build_qa(vectordb):
    retriever = vectordb.as_retriever(search_kwargs={"k": 3})
    llm = get_llm()
    qa = RetrievalQA.from_chain_type(
        llm=llm,
        retriever=retriever,
        chain_type="stuff"
    )
    return qa


# === 6. Run the Query ===
if __name__ == "__main__":
    print("Loading documents...")
    docs = load_documents("data")

    print("Splitting...")
    chunks = split_documents(docs)

    print("Creating vector store...")
    vectordb = create_vector_store(chunks)

    print("Starting local RAG session...")
    qa = build_qa(vectordb)

    while True:
        query = input("\nAsk something (or type 'exit'): ")
        if query.lower() == "exit":
            break
        result = qa.run(query)
        print("\nAnswer:", result)
