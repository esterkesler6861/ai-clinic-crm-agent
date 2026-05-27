from graph_state import ClinicCRMState
from rag.answering import answer_from_knowledge
from utils import add_log
from workflow_nodes.logging_utils import with_log


def knowledge_request_node(state: ClinicCRMState):
    state = with_log(
        state,
        f"NODE knowledge_request_node | text={state.get('user_input')}",
    )

    answer, rag_logs = answer_from_knowledge(
        state["user_input"],
        return_logs=True,
    )

    for message in rag_logs:
        state = with_log(state, message)

    return {
        **state,
        "active_flow": None,
        "tool_result": answer,
        "logs": add_log(state, "KNOWLEDGE REQUEST ANSWERED FROM RAG"),
    }


__all__ = [
    "knowledge_request_node",
]