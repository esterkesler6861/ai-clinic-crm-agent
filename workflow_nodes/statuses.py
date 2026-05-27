from graph_state import ClinicCRMState
from workflow_nodes.logging_utils import with_log
from tools import get_form17_status, get_referral_status
from utils import add_log, extract_first_number, extract_form17_id


def referral_status_node(state: ClinicCRMState):
    state = with_log(
        state,
        f"NODE referral_status_node | text={state.get('user_input')}",
    )

    referral_id = extract_first_number(state["user_input"])

    state = with_log(
        state,
        f"REFERRAL ID EXTRACTED | referral_id={referral_id}",
    )

    if not referral_id:
        return {
            **state,
            "active_flow": "referral_status",
            "waiting_for_referral_id": True,
            "tool_result": None,
            "logs": add_log(state, "REFERRAL STATUS NEEDS ID"),
        }

    tool_result = get_referral_status(referral_id)

    return {
        **state,
        "referral_id": referral_id,
        "active_flow": None,
        "last_completed_flow": "referral_status",
        "waiting_for_referral_id": False,
        "tool_result": tool_result,
        "logs": add_log(state, f"REFERRAL STATUS RESULT | result={tool_result}"),
    }


def form17_status_node(state: ClinicCRMState):
    state = with_log(
        state,
        f"NODE form17_status_node | text={state.get('user_input')}",
    )

    form17_id = extract_form17_id(state["user_input"])

    state = with_log(
        state,
        f"FORM17 ID EXTRACTED | form17_id={form17_id}",
    )

    if not form17_id:
        return {
            **state,
            "active_flow": "form17_status",
            "waiting_for_form17_id": True,
            "tool_result": None,
            "logs": add_log(
                state,
                "לא נמצאה התחייבות עם המספר שלחת. אנא וודא שהמספר שהזנת נכון ונסה שוב.",
            ),
        }

    tool_result = get_form17_status(form17_id)

    return {
        **state,
        "form17_id": form17_id,
        "active_flow": None,
        "last_completed_flow": "form17_status",
        "waiting_for_form17_id": False,
        "tool_result": tool_result,
        "logs": add_log(state, f"FORM17 STATUS RESULT | result={tool_result}"),
    }
