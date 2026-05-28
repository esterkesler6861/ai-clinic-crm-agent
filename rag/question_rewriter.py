from openai import OpenAI
from utils import build_history_text

client = OpenAI()


def rewrite_knowledge_question(state) -> str:
    history_text = build_history_text(state)

    current_question = state["user_input"]

    prompt = f"""
You are a strict conversational query rewriter for a clinic assistant.

Your job:
Rewrite the user's latest message into a standalone question ONLY when needed.

Critical rules:
- Do NOT answer the question.
- Do NOT add assumptions.
- Do NOT add entities that were not explicitly mentioned or clearly implied.
- Do NOT add "your clinic", "our clinic", "center", "medical center", or similar ownership/context unless the user explicitly said it.
- Preserve the exact semantic meaning of the latest user message.
- If the latest user message is already standalone, return it unchanged.
- If the conversation is about urgent care centers, preserve the exact term "מוקד לרפואה דחופה".
- Do NOT replace medical/clinic terms with broader terms.
- Return ONLY the rewritten standalone question.

Conversation history:
{history_text}

Latest user message:
{current_question}

Standalone question:
"""

    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        temperature=0,
        messages=[
            {
                "role": "system",
                "content": "Rewrite conversational follow-up questions into standalone questions.",
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
    )

    return response.choices[0].message.content.strip()