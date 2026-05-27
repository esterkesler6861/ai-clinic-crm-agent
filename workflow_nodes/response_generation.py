from graph_state import ClinicCRMState
from models import model
from prompts import format_general_feedback_prompt, format_workflow_response_prompt
from utils import add_log, build_history_text, detect_language
from workflow_nodes.logging_utils import with_log


def generate_response_node(state: ClinicCRMState):
    state = with_log(
        state,
        f"NODE generate_response_node | intent={state.get('intent')} | active_flow={state.get('active_flow')} | pending_action={state.get('pending_action')}",
    )
    history_text = build_history_text(state)
    if state.get("waiting_for_specialty", False):
        return {
            **state,
            "answer": "לאיזה תחום ברצונך לקבוע תור? למשל: קרדיולוגיה, אורתופדיה, עור, משפחה או ילדים.",
            "logs": add_log(state, "RESPONSE MODE | waiting_for_specialty"),
        }
    if state.get("tool_result") == "show_available_slots_again":
        return {
            **state,
            "answer": "אלו המועדים הפנויים כרגע. אפשר לבחור אחד מהם.",
            "logs": add_log(state, "RESPONSE MODE | show_available_slots_again"),
        }
    if state.get("tool_result") == "slot_not_found":
        return {
            **state,
            "answer": "לא מצאתי את המועד שבחרת. אפשר לבחור אחד מהמועדים שמופיעים בכפתורים.",
            "logs": add_log(state, "RESPONSE MODE | slot_not_found"),
        }

    if state.get("waiting_for_time_selection", False):
        return {
            **state,
            "answer": "מצאתי כמה תורים פנויים. יש לבחור אחד מהמועדים שמופיעים כאן.",
            "logs": add_log(state, "RESPONSE MODE | waiting_for_time_selection"),
        }

    if state.get("waiting_for_appointment_selection", False):
        return {
            **state,
            "answer": "מצאתי את התורים הפעילים שלך. יש לבחור איזה תור לבטל.",
            "logs": add_log(state, "RESPONSE MODE | waiting_for_appointment_selection"),
        }

    if state.get("waiting_for_confirmation", False):
        pending_action = state.get("pending_action")
        pending_data = state.get("pending_data") or {}

        state = with_log(
            state,
            f"RESPONSE MODE | waiting_for_confirmation | action={pending_action}",
        )

        if pending_action == "book_appointment":
            specialty = pending_data.get("specialty") or state.get("specialty")
            slot = pending_data.get("slot") or state.get("selected_slot")

            return {
                **state,
                "answer": f"לאשר את התור ל־{specialty} במועד {slot}?",
                "logs": add_log(state, "ASK CONFIRMATION | book_appointment"),
            }

        if pending_action == "cancel_appointment":
            specialty = pending_data.get("specialty")
            slot = pending_data.get("slot")
            appointment_id = pending_data.get("appointment_id")

            return {
                **state,
                "answer": f"לאשר ביטול של תור {appointment_id} ל־{specialty} במועד {slot}?",
                "logs": add_log(state, "ASK CONFIRMATION | cancel_appointment"),
            }

        return {
            **state,
            "answer": "לאשר את הפעולה?",
            "logs": add_log(state, "ASK CONFIRMATION | generic"),
        }

    if state.get("tool_result") == "confirmation_rejected":
        return {
            **state,
            "answer": "בסדר, הפעולה לא בוצעה.",
            "logs": add_log(state, "RESPONSE MODE | confirmation_rejected"),
        }
    if state.get("tool_result") == "flow_cancelled":
        return {
        **state,
        "answer": "בסדר גמור, יצאתי מהתהליך. אפשר להתחיל פעולה חדשה.",
        "logs": add_log(state, "RESPONSE MODE | flow_cancelled"),
    }

    if state.get("intent") == "general_feedback":
        response = model.invoke(
            format_general_feedback_prompt(user_input=state.get("user_input"))
        )

        return {
            **state,
            "answer": response.content,
            "logs": add_log(state, "GENERAL FEEDBACK RESPONSE GENERATED"),
        }

    if state.get("intent") == "unsupported_topic":
        return {
            **state,
            "answer": "אני יכולה לעזור רק בפעולות של המרפאה: קביעת תור, ביטול תור, סטטוס הפניה או טופס 17.",
            "logs": add_log(state, "RESPONSE MODE | unsupported_topic"),
        }
    if state.get("intent") == "unknown":
        return {
            **state,
            "answer": "אשמח לעזור. אפשר לקבוע תור, לבטל תור, לבדוק סטטוס הפניה או טופס 17. למה התכוונת?",
            "logs": add_log(state, "RESPONSE MODE | deterministic unknown response"),
        }

    if state.get("tool_result"):
        return {
            **state,
            "answer": str(state.get("tool_result")),
            "logs": add_log(state, "RESPONSE MODE | tool_result"),
        }

    state = with_log(state, "RESPONSE MODE | ai_general_workflow_response")

    language = detect_language(state["user_input"])

    response = model.invoke(
        format_workflow_response_prompt(
            history_text=history_text,
            language=language,
            user_input=state.get("user_input"),
            intent=state.get("intent"),
            active_flow=state.get("active_flow"),
            pending_action=state.get("pending_action"),
            pending_data=state.get("pending_data"),
            specialty=state.get("specialty"),
            available_slots=state.get("available_slots"),
            selected_slot=state.get("selected_slot"),
            available_appointments=state.get("available_appointments"),
            selected_appointment_id=state.get("selected_appointment_id"),
            appointment_id=state.get("appointment_id"),
            referral_id=state.get("referral_id"),
            form17_id=state.get("form17_id"),
            waiting_for_specialty=state.get("waiting_for_specialty", False),
            waiting_for_time_selection=state.get("waiting_for_time_selection", False),
            waiting_for_appointment_selection=state.get(
                "waiting_for_appointment_selection", False
            ),
            waiting_for_confirmation=state.get("waiting_for_confirmation", False),
            waiting_for_appointment_id=state.get("waiting_for_appointment_id", False),
            waiting_for_referral_id=state.get("waiting_for_referral_id", False),
            waiting_for_form17_id=state.get("waiting_for_form17_id", False),
            needs_human=state.get("needs_human", False),
        )
    )

    return {
        **state,
        "answer": response.content,
        "logs": add_log(state, "AI WORKFLOW RESPONSE GENERATED"),
    }


__all__ = [
    "generate_response_node",
]
