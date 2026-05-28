from graph_state import ClinicCRMState
from utils import add_log
from workflow_nodes.logging_utils import with_log


def update_message_history_node(state: ClinicCRMState):
    state = with_log(state, "NODE update_message_history_node")

    # הcheckpointer שומר את messages בין טורנים —
    # כאן אנחנו מוסיפים את הטורן הנוכחי (user + assistant) לסוף הרשימה.
    messages = list(state.get("messages") or [])

    user_input = state.get("user_input", "").strip()
    answer = state.get("answer", "").strip()

    # הוסף הודעת user רק אם היא לא כבר ההודעה האחרונה (למניעת כפילויות)
    if user_input:
        if not messages or messages[-1].get("content") != user_input or messages[-1].get("role") != "user":
            messages.append({"role": "user", "content": user_input})

    # הוסף תשובת הבוט
    if answer:
        messages.append({"role": "assistant", "content": answer})

    # שמור רק 20 הודעות אחרונות (10 טורנים) כדי לא לנפח את ה-state
    messages = messages[-20:]

    return {
        **state,
        "messages": messages,
        "logs": add_log(state, f"MESSAGES UPDATED | total={len(messages)}"),
    }


__all__ = ["update_message_history_node"]