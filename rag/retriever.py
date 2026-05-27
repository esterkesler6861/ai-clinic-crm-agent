from dotenv import load_dotenv

load_dotenv()

from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma

from rag.config import (
    CHROMA_DIR,
    EMBEDDING_MODEL,
)


embeddings = OpenAIEmbeddings(
    model=EMBEDDING_MODEL
)

vector_store = Chroma(
    persist_directory=str(CHROMA_DIR),
    embedding_function=embeddings,
)


def retrieve_context(query: str, k: int = 3):
    results = vector_store.similarity_search(
        query=query,
        k=k,
    )

    return results


if __name__ == "__main__":

    question = "עד מתי אפשר לבטל תור?"

    docs = retrieve_context(question)

    print("\nQUESTION:")
    print(question)

    print("\nRESULTS:")
    print("=" * 50)

    for index, doc in enumerate(docs, start=1):
        print(f"\nRESULT #{index}")
        print(doc.page_content)