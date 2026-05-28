from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

KNOWLEDGE_DIR = BASE_DIR / "rag" / "knowledge"
CHROMA_DIR = BASE_DIR / "rag" / "chroma_db"

EMBEDDING_MODEL = "text-embedding-3-small"

CHUNK_SIZE = 500
CHUNK_OVERLAP = 80