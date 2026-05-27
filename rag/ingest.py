from dotenv import load_dotenv
import shutil
from pathlib import Path
load_dotenv()
from pathlib import Path

from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma

from rag.config import (
    KNOWLEDGE_DIR,
    CHROMA_DIR,
    EMBEDDING_MODEL,
    CHUNK_SIZE,
    CHUNK_OVERLAP,
)


def load_documents():
    documents = []

    for file_path in Path(KNOWLEDGE_DIR).glob("*"):
        if file_path.suffix.lower() == ".pdf":
            loader = PyPDFLoader(str(file_path))
            documents.extend(loader.load())

        elif file_path.suffix.lower() == ".txt":
            loader = TextLoader(str(file_path), encoding="utf-8")
            documents.extend(loader.load())

    return documents


def split_documents(documents):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
    )

    return splitter.split_documents(documents)


def ingest_knowledge():
    if CHROMA_DIR.exists():
        shutil.rmtree(CHROMA_DIR)

    documents = load_documents()

    if not documents:
        return {
            "status": "empty",
            "message": "לא נמצאו מסמכים בתיקיית knowledge.",
            "documents": 0,
            "chunks": 0,
        }

    chunks = split_documents(documents)

    embeddings = OpenAIEmbeddings(model=EMBEDDING_MODEL)

    Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=str(CHROMA_DIR),
    )

    return {
        "status": "success",
        "documents": len(documents),
        "chunks": len(chunks),
        "message": "הידע נטען ונשמר בהצלחה.",
    }

if __name__ == "__main__":
    result = ingest_knowledge()
    print(result)