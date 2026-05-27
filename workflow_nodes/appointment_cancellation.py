from graph_state import ClinicCRMState
from tools import get_patient_appointments
from utils import add_log
from workflow_nodes.logging_utils import with_log


def cancel_appointment_node(state: ClinicCRMState):
    state = with_log(state, "NODE cancel_appointment_node")

    patient_id = state.get("patient_id") or "demo-patient-123"
    appointments = get_patient_appointments(patient_id)

    state = with_log(
        state,
        f"PATIENT APPOINTMENTS | patient_id={patient_id} | count={len(appointments)}",
    )

    if not appointments:
        return {
            **state,
            "active_flow": None,
            "available_appointments": [],
            "waiting_for_appointment_selection": False,
            "tool_result": "לא נמצאו תורים פעילים לביטול.",
            "logs": add_log(state, "NO APPOINTMENTS TO CANCEL"),
        }

    return {
        **state,
        "active_flow": "cancel_appointment",
        "available_appointments": appointments,
        "waiting_for_appointment_selection": True,
        "tool_result": "מצאתי את התורים הפעילים שלך. בחרי איזה תור לבטל.",
        "logs": add_log(state, "CANCELLATION WAITING FOR APPOINTMENT SELECTION"),
    }


def select_appointment_to_cancel_node(state: ClinicCRMState):
    state = with_log(
        state,
        f"NODE select_appointment_to_cancel_node | text={state.get('user_input')}",
    )

    user_text = state["user_input"]
    selected_appointment = None

    for appointment in state.get("available_appointments") or []:
        appointment_id = appointment["appointment_id"]

        if appointment_id in user_text:
            selected_appointment = appointment
            break

    state = with_log(
        state,
        f"APPOINTMENT SELECTED FOR CANCEL | appointment={selected_appointment}",
    )

    if not selected_appointment:
        return {
            **state,
            "tool_result": "לא הצלחתי לזהות איזה תור לבטל. בחרי אחד מהתורים שמוצגים.",
            "logs": add_log(state, "APPOINTMENT TO CANCEL NOT FOUND"),
        }

    return {
        **state,
        "selected_appointment_id": selected_appointment["appointment_id"],
        "waiting_for_appointment_selection": False,
        "waiting_for_confirmation": True,
        "pending_action": "cancel_appointment",
        "pending_data": selected_appointment,
        "tool_result": None,
        "logs": add_log(
            state,
            f"CANCELLATION WAITING FOR CONFIRMATION | appointment_id={selected_appointment['appointment_id']}",
        ),
    }
