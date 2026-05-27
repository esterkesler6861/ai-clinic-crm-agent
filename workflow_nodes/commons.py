import logging

from graph_state import ClinicCRMState
from workflow_nodes.logging_utils import with_log
from tools import book_appointment, cancel_appointment
from utils import add_log

logger = logging.getLogger(__name__)


def unsupported_topic_node(state: ClinicCRMState):
    state = with_log(
        state,
        f"NODE unsupported_topic_node | text={state.get('user_input')}",
    )

    return {
        **state,
        "active_flow": None,
        "tool_result": None,
        "logs": add_log(state, "UNSUPPORTED TOPIC INTENT"),
    }


def general_feedback_node(state: ClinicCRMState):
    state = with_log(
        state,
        f"NODE general_feedback_node | text={state.get('user_input')}",
    )

    return {
        **state,
        "active_flow": None,
        "tool_result": None,
        "logs": add_log(state, "GENERAL FEEDBACK INTENT"),
    }


def confirm_action_node(state: ClinicCRMState):
    state = with_log(
        state,
        f"NODE confirm_action_node | pending_action={state.get('pending_action')}",
    )

    pending_action = state.get("pending_action")
    pending_data = state.get("pending_data") or {}

    if pending_action == "book_appointment":
        slot = pending_data.get("slot")
        specialty = pending_data.get("specialty")

        state = with_log(
            state,
            f"CONFIRM BOOK APPOINTMENT | specialty={specialty} | slot={slot}",
        )

        booking_result = book_appointment(
            patient_id=state.get("patient_id"),
            specialty=specialty,
            slot=slot,
        )

        return {
            **state,
            "active_flow": None,
            "waiting_for_specialty": False,
            "waiting_for_time_selection": False,
            "waiting_for_confirmation": False,
            "pending_action": None,
            "pending_data": None,
            "available_slots": None,
            "selected_slot": slot,
            "tool_result": booking_result,
            "logs": add_log(state, "BOOK APPOINTMENT COMPLETED"),
        }

    if pending_action == "cancel_appointment":
        appointment_id = pending_data.get("appointment_id")

        state = with_log(
            state,
            f"CONFIRM CANCEL APPOINTMENT | appointment_id={appointment_id}",
        )

        cancel_result = cancel_appointment(appointment_id)

        state = with_log(
            state,
            f"CANCEL RESULT | result={cancel_result}",
        )

        return {
            **state,
            "active_flow": None,
            "waiting_for_confirmation": False,
            "waiting_for_appointment_selection": False,
            "pending_action": None,
            "pending_data": None,
            "selected_appointment_id": appointment_id,
            "available_appointments": None,
            "tool_result": cancel_result,
            "logs": add_log(state, "CANCEL APPOINTMENT COMPLETED"),
        }

    logger.warning("CONFIRM ACTION WITHOUT PENDING ACTION")

    return {
        **state,
        "waiting_for_confirmation": False,
        "pending_action": None,
        "pending_data": None,
        "tool_result": "לא נמצאה פעולה שממתינה לאישור.",
        "logs": add_log(state, "CONFIRM ACTION WITHOUT PENDING ACTION"),
    }


def cancel_confirmation_node(state: ClinicCRMState):
    state = with_log(
        state,
        f"NODE cancel_confirmation_node | pending_action={state.get('pending_action')}",
    )

    pending_action = state.get("pending_action")

    if pending_action == "cancel_appointment":
        return {
            **state,
            "waiting_for_confirmation": False,
            "waiting_for_appointment_selection": True,
            "pending_action": None,
            "pending_data": None,
            "tool_result": "בסדר, לא ביטלתי את התור. אפשר לבחור תור אחר לביטול.",
            "logs": add_log(
                state, "CANCEL CONFIRMATION REJECTED | back to appointment selection"
            ),
        }

    return {
        **state,
        "waiting_for_confirmation": False,
        "pending_action": None,
        "pending_data": None,
        "tool_result": "בסדר, הפעולה לא בוצעה.",
        "logs": add_log(state, "CONFIRMATION REJECTED"),
    }


def human_escalation_node(state: ClinicCRMState):
    state = with_log(state, "NODE human_escalation_node")

    return {
        **state,
        "needs_human": True,
        "active_flow": None,
        "tool_result": "מעבירים אותך לנציג אנושי , זה עלול לקחת כמה רגעים. תודה על הסבלנות.",
        "logs": add_log(state, "HUMAN ESCALATION REQUIRED"),
    }


def unknown_node(state: ClinicCRMState):
    state = with_log(
        state,
        f"NODE unknown_node | text={state.get('user_input')}",
    )

    return {
        **state,
        "active_flow": None,
        "tool_result": None,
        "answer": None,
        "intent": "unknown",
        "logs": add_log(state, "UNKNOWN INTENT | moving to general response"),
    }
