import logging
from graph_state import ClinicCRMState
logger = logging.getLogger(__name__)

def with_log(state: ClinicCRMState, message: str):
    logger.info(message)
    return {
        **state,
        "logs": add_log(state, message),
    }

def add_log(state, message: str):
    logs = state.get("logs") or []

    logs.append(message)

    # keep only last 20 logs
    return logs[-20:]

def build_history_text(state, limit: int = 10):
    history = state.get("messages") or []
    if not history:
        return "No previous conversation."
    return "\n".join(
        f"{msg.get('role')}: {msg.get('content')}"
        for msg in history[-limit:]
    )