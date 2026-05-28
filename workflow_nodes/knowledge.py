from graph_state import ClinicCRMState
from rag.answering import answer_from_knowledge
from rag.question_rewriter import rewrite_knowledge_question
from utils import add_log
from workflow_nodes.logging_utils import with_log


def knowledge_request_node(state: ClinicCRMState):
    state = with_log(
        state,
        f"NODE knowledge_request_node | text={state.get('user_input')}",
    )

    rewritten_question = rewrite_knowledge_question(state)

    state = with_log(
        state,
        (
            f"RAG | original_question={state['user_input']} "
            f"| rewritten_question={rewritten_question}"
        ),
    )

    question = f"""
תאריך ושעה נוכחיים בישראל:
{state.get("current_datetime")}

יום בשבוע:
{state.get("current_weekday")}

שעה:
{state.get("current_time")}

שאלת המשתמש:
{rewritten_question}
"""

    state = with_log(
        state,
        f"RAG | final_question={question}",
    )

    answer, rag_logs = answer_from_knowledge(
        question,
        return_logs=True,
    )

    for message in rag_logs:
        state = with_log(state, message)

    return {
        **state,
        "active_flow": None,
        "tool_result": answer,
        "logs": add_log(
            state,
            "KNOWLEDGE REQUEST ANSWERED FROM RAG",
        ),
    }


__all__ = [
    "knowledge_request_node",
]