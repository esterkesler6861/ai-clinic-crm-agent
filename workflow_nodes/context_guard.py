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

logger = logging.getLogger("nodes")


def _invoke_flow_decision(state, text, history_text, **overrides):
    kwargs = dict(
        active_flow=state.get("active_flow"),
        waiting_for_specialty=state.get("waiting_for_specialty", False),
        waiting_for_time_selection=state.get("waiting_for_time_selection", False),
        waiting_for_confirmation=state.get("waiting_for_confirmation", False),
        waiting_for_appointment_id=state.get("waiting_for_appointment_id", False),
        waiting_for_referral_id=state.get("waiting_for_referral_id", False),
        waiting_for_form17_id=state.get("waiting_for_form17_id", False),
        waiting_for_appointment_selection=state.get("waiting_for_appointment_selection", False),
        available_slots=state.get("available_slots"),
        available_appointments=state.get("available_appointments"),
        selected_slot=state.get("selected_slot"),
        pending_action=state.get("pending_action"),
        text=text,
        history_text=history_text,
    )
    kwargs.update(overrides)
    return flow_decision_model.invoke(format_context_guard_prompt(**kwargs))


def _off_topic_response(state, label):
    return {
        **state,
        "intent": "unknown",
        "tool_result": "off_topic_during_flow",
        "logs": add_log(state, f"CONTEXT GUARD | off_topic during {label}"),
    }


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
            "logs": add_log(new_state, f"STATE RESET FOR NEW FLOW | flow={explicit_new_flow}"),
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
        state = {
            **state,
            "resolved_user_input": None,
            "entities": None,
        }
        return with_log(state, "NO ACTIVE WAITING STATE")

    # קיצור דטרמיניסטי: specialty ידועה → המשך flow
    if state.get("waiting_for_specialty", False):
         specialty = extract_specialty(text)
         if specialty:
             state = with_log(state, f"CONTEXT GUARD | specialty detected={specialty}")
             return {
                 **state,
                 "tool_result": None,
                 "resolved_user_input": text,
                 "is_followup": True,
                 }

    # waiting_for_time_selection: בדוק עם AI
    if state.get("waiting_for_time_selection", False):
        result = _invoke_flow_decision(state, text, history_text)
        state = with_log(
            state,
            f"CONTEXT GUARD time_selection | continue={result.continue_current_flow} | reason={result.reason}",
        )
        if result.continue_current_flow:
            
          return {
         **state,
        "tool_result": None,
        "resolved_user_input": text,
        "is_followup": True,
    }
        return _off_topic_response(state, "time_selection")

    # waiting_for_confirmation: בדוק עם AI
    if state.get("waiting_for_confirmation", False):
        result = _invoke_flow_decision(state, text, history_text)
        state = with_log(
            state,
            f"CONTEXT GUARD confirmation | continue={result.continue_current_flow} | reason={result.reason}",
        )
       
        if result.continue_current_flow:
            return {
        **state,
        "tool_result": None,
        "resolved_user_input": text,
        "is_followup": True,
    }
        return _off_topic_response(state, "confirmation")

    # שאר מצבי המתנה
    result = _invoke_flow_decision(state, text, history_text)
    state = with_log(
        state,
        f"CONTEXT DECISION | continue_current_flow={result.continue_current_flow}",
    )

    if result.continue_current_flow:
        return {
        **state,
        "tool_result": None,
        "resolved_user_input": text,
        "is_followup": True,
    }

    new_state = reset_state(state)
    return {
        **new_state,
        "logs": add_log(new_state, "CONTEXT GUARD RESETTING STATE"),
    }


__all__ = [
    "context_guard_node",
]