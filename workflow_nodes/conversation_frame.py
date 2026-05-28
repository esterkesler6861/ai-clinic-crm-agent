from copy import deepcopy
from graph_state import ClinicCRMState
from nodes_shared import with_log
def conversation_frame_node(state: ClinicCRMState):
    text = state.get("user_input", "")
    state = with_log(
        state,
        f"NODE conversation_frame_node | text={state.get('user_input')}"
    )
    frame = get_frame(state)
    followup = is_followup_message(text)

    return {
        **state,
        "conversation_frame": frame,
        "resolved_user_input": text,
        "is_followup": followup,
    }

DEFAULT_FRAME = {
    "topic": None,
    "intent": None,
    "entities": {
        "city": None,
        "specialty": None,
        "date": None,
        "time_of_day": None,
        "service": None,
    },
}


def get_frame(state):
    frame = state.get("conversation_frame")

    if not frame:
        return deepcopy(DEFAULT_FRAME)

    return deepcopy(frame)


def update_frame(
    state,
    topic=None,
    intent=None,
    entities=None,
):
    frame = get_frame(state)

    if topic:
        frame["topic"] = topic

    if intent:
        frame["intent"] = intent

    if entities:
        for key, value in entities.items():
            if value is not None:
                frame["entities"][key] = value

    return frame

def is_followup_message(text: str) -> bool:
    text = text.strip()

    short_followups = [
        "וב",
        "ומה",
        "ול",
        "גם",
    ]

    if len(text.split()) <= 4:
        return True

    return any(text.startswith(prefix) for prefix in short_followups)