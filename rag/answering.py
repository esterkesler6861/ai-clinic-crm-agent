from dotenv import load_dotenv

load_dotenv()

from langchain_openai import ChatOpenAI

from rag.retriever import retrieve_context


model = ChatOpenAI(
    model="gpt-4.1-mini",
    temperature=0,
)


def build_context(docs):
    return "\n\n".join(doc.page_content for doc in docs)


def answer_from_knowledge(
    question: str,
    *,
    return_logs: bool = False,
    debug: bool = False,
):
    """Answer a clinic knowledge question using retrieved RAG context.

    - Default: returns `answer: str`.
    - If `return_logs=True`: returns `(answer, logs)` where logs is a list of short
      debug lines explaining *why* the answer was produced (what was retrieved, etc.).
    - If `debug=True`: returns `(answer, debug_info)` (legacy/dev mode).
    """

    logs: list[str] = []

    k = 5
    logs.append(f"RAG | retrieve_context | k={k}")
    docs = retrieve_context(question, k=k)
    logs.append(f"RAG | retrieved_docs={len(docs)}")

    # Log a short preview of the retrieved sources to help understand why the model answered.
    for i, doc in enumerate(docs, start=1):
        metadata = getattr(doc, "metadata", None) or {}
        source = (
            metadata.get("source")
            or metadata.get("file")
            or metadata.get("path")
            or metadata.get("url")
            or "unknown_source"
        )
        preview = (doc.page_content or "").replace("\n", " ").strip()
        if len(preview) > 160:
            preview = preview[:160] + "..."

        logs.append(f"RAG | doc#{i} | source={source} | preview={preview}")

    context = build_context(docs)
    logs.append(f"RAG | context_chars={len(context)}")

    prompt = f"""
את עוזרת מידע של מרפאה.

עני רק לפי ההקשר.
אם אין מידע בהקשר, כתבי בדיוק:
"אין לי מידע על זה במסמכי המרפאה."

אם קיימת רשימת נתונים רלוונטית אך הפריט שהמשתמש ביקש לא מופיע בה,
יש לענות שלא נמצא מידע ספציפי עבור אותו פריט,
ולא לומר שאין מידע במסמכים.

דוגמא:
אם המשתמש שואל על מוקד בלוד,
ויש מסמך מוקדים אך לוד לא מופיעה בו,
ענה:
"לא מצאתי מוקד לרפואה דחופה בלוד."
ולא:
"אין לי מידע במסמכים."

אם המשתמש שואל "אלו", "איזה", "מה הם", או מבקש רשימה:
- החזירי רשימה של כל הפריטים שמופיעים בהקשר
- אל תעני תשובה כללית כמו "יש מוקדים"
- אם מופיע רק פריט אחד, כתבי רק אותו
- אם אין פירוט שמות/כתובות/פרטים, כתבי שאין פירוט במסמכי המרפאה

הקשר:
{context}

שאלה:
{question}

תשובה:
"""

    logs.append("RAG | invoking_model")
    response = model.invoke(prompt)
    answer = response.content.strip()
    logs.append(f"RAG | answer_chars={len(answer)}")

    if debug:
        return answer, {
            "docs_count": len(docs),
            "docs": [doc.page_content for doc in docs],
        }

    if return_logs:
        return answer, logs

    return answer


if __name__ == "__main__":
    question = "עד מתי אפשר לבטל תור?"
    answer = answer_from_knowledge(question)

    print("\nQUESTION:")
    print(question)

    print("\nANSWER:")
    print(answer)