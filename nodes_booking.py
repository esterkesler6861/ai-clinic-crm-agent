import logging

from graph_state import ClinicCRMState
from tools import get_available_appointments
from utils import extract_specialty, add_log, build_history_text
from ai_helpers import resolve_slot_with_ai
from nodes_shared import with_log


def book_appointment_node(state: ClinicCRMState):
    state = with_log(
        state,
        f"NODE book_appointment_node | text={state.get('user_input')}",
    )

    specialty = extract_specialty(state["user_input"])

    state = with_log(
        state,
        f"SPECIALTY EXTRACTED | specialty={specialty}",
    )

    if not specialty:
        return {
            **state,
            "active_flow": "book_appointment",
            "waiting_for_specialty": True,
            "waiting_for_time_selection": False,
            "waiting_for_confirmation": False,
            "tool_result": None,
            "logs": add_log(state, "BOOKING NEEDS SPECIALTY"),
        }

    available_slots = get_available_appointments(specialty)

    state = with_log(
        state,
        f"AVAILABLE SLOTS | specialty={specialty} | slots={available_slots}",
    )

    if not available_slots:
        return {
            **state,
            "specialty": specialty,
            "last_topic": "doctor_availability",
            "last_entities": {
                "specialty": specialty,
            },
            "active_flow": None,
            "waiting_for_specialty": False,
            "waiting_for_time_selection": False,
            "waiting_for_confirmation": False,
            "available_slots": None,
            "tool_result": "לא נמצאו תורים פנויים לתחום הזה.",
            "logs": add_log(state, "NO AVAILABLE SLOTS"),
        }

    return {
        **state,
        "specialty": specialty,
        "last_topic": "doctor_availability",
        "last_entities": {
            "specialty": specialty,
        },
        "active_flow": "book_appointment",
        "waiting_for_specialty": False,
        "waiting_for_time_selection": True,
        "waiting_for_confirmation": False,
        "available_slots": available_slots,
        "selected_slot": None,
        "pending_action": None,
        "pending_data": None,
        "tool_result": None,
        "logs": add_log(state, "BOOKING WAITING FOR SLOT SELECTION"),
    }


def select_appointment_slot_node(state: ClinicCRMState):
    state = with_log(
        state,
        f"NODE select_appointment_slot_node | text={state.get('user_input')}",
    )

    user_text = state["user_input"].strip().lower()
    available_slots = state.get("available_slots") or []

    matching_slot = None

    for slot in available_slots:
        normalized_slot = slot.lower()

        if (
            user_text == normalized_slot
            or user_text in normalized_slot
            or normalized_slot in user_text
        ):
            matching_slot = slot
            break

    state = with_log(
        state,
        f"SLOT MATCH RESULT | matching_slot={matching_slot}",
    )

    if not matching_slot:
        history_text = build_history_text(state)

        ai_result = resolve_slot_with_ai(
            user_text=user_text,
            available_slots=available_slots,
            history_text=history_text,
        )

        state = with_log(
            state,
            f"AI SLOT RESOLUTION | result={ai_result}",
        )

        if ai_result in available_slots:
            matching_slot = ai_result

        elif ai_result == "show_options":
            return {
                **state,
                "waiting_for_time_selection": True,
                "waiting_for_confirmation": False,
                "tool_result": "show_available_slots_again",
                "logs": add_log(state, "AI REQUESTED SLOT OPTIONS AGAIN"),
            }

        else:
            return {
                **state,
                "waiting_for_time_selection": True,
                "waiting_for_confirmation": False,
                "tool_result": "slot_not_found",
                "logs": add_log(state, "AI COULD NOT RESOLVE SLOT"),
            }

    return {
        **state,
        "selected_slot": matching_slot,
        "waiting_for_time_selection": False,
        "waiting_for_confirmation": True,
        "pending_action": "book_appointment",
        "pending_data": {
            "slot": matching_slot,
            "specialty": state.get("specialty"),
            "patient_id": state.get("patient_id"),
        },
        "tool_result": None,
        "logs": add_log(state, f"SLOT SELECTED | slot={matching_slot}"),
    }