import logging

from graph_state import ClinicCRMState
from models import flow_decision_model
from prompts import format_context_guard_prompt
from utils import (
    add_log,
    build_history_text,
    detect_explicit_new_flow,
    extract_specialty,
    reset_state,
    should_reset_by_text,
)
from workflow_nodes.logging_utils import with_log

# Keep legacy logger name used by `nodes.py` (module name `nodes`).
logger = logging.getLogger("nodes")


def context_guard_node(state: ClinicCRMState):

    state = with_log(
        state,
        f"NODE context_guard_node | text={state.get('user_input')} | active_flow={state.get('active_flow')}",
    )

    history_text = build_history_text(state)
    text = state["user_input"]
    explicit_new_flow = detect_explicit_new_flow(text)

    if explicit_new_flow and explicit_new_flow != state.get("active_flow"):
        state = with_log(
            state,
            f"EXPLICIT FLOW SWITCH | from={state.get('active_flow')} | to={explicit_new_flow}",
        )

        new_state = reset_state(state)

        return {
            **new_state,
            "user_input": text,
            "logs": add_log(
                new_state,
                f"STATE RESET FOR NEW FLOW | flow={explicit_new_flow}",
            ),
        }

    if should_reset_by_text(text):
        state = with_log(state, "RESET REQUEST DETECTED")
        new_state = reset_state(state)

        return {
        **new_state,
        "intent": "general_feedback",
        "tool_result": "flow_cancelled",
        "logs": add_log(new_state, "STATE RESET BY USER TEXT"),
    }

    has_active_waiting = (
        state.get("waiting_for_specialty", False)
        or state.get("waiting_for_time_selection", False)
        or state.get("waiting_for_confirmation", False)
        or state.get("waiting_for_appointment_id", False)
        or state.get("waiting_for_referral_id", False)
        or state.get("waiting_for_form17_id", False)
        or state.get("waiting_for_appointment_selection", False)
    )

    if not has_active_waiting:
        return with_log(state, "NO ACTIVE WAITING STATE")

    # Deterministic shortcut:
    # If the graph is waiting for a specialty and the user gave a known specialty,
    # continue the current flow without asking the AI context guard.
    if state.get("waiting_for_specialty", False):
        specialty = extract_specialty(text)

        if specialty:
            return with_log(
                state,
                f"CONTEXT GUARD | specialty detected={specialty}",
            )
    if state.get("waiting_for_time_selection", False):
        return with_log(
            state,
            "CONTEXT GUARD | waiting_for_time_selection - continue current flow",
        )

    result = flow_decision_model.invoke(
        format_context_guard_prompt(
            active_flow=state.get("active_flow"),
            waiting_for_specialty=state.get("waiting_for_specialty", False),
            waiting_for_time_selection=state.get("waiting_for_time_selection", False),
            waiting_for_confirmation=state.get("waiting_for_confirmation", False),
            waiting_for_appointment_id=state.get("waiting_for_appointment_id", False),
            waiting_for_referral_id=state.get("waiting_for_referral_id", False),
            waiting_for_form17_id=state.get("waiting_for_form17_id", False),
            waiting_for_appointment_selection=state.get(
                "waiting_for_appointment_selection", False
            ),
            available_slots=state.get("available_slots"),
            available_appointments=state.get("available_appointments"),
            selected_slot=state.get("selected_slot"),
            pending_action=state.get("pending_action"),
            text=text,
            history_text=history_text,
        )
    )

    state = with_log(
        state,
        f"CONTEXT DECISION | continue_current_flow={result.continue_current_flow}",
    )

    if result.continue_current_flow:
        return state

    new_state = reset_state(state)

    return {
        **new_state,
        "logs": add_log(new_state, "CONTEXT GUARD RESETTING STATE"),
    }


__all__ = [
    "context_guard_node",
]
