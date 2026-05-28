import re
from datetime import datetime

from graph_state import ClinicCRMState
from ai_helpers import ai_confirmation_check


def reset_state(state: ClinicCRMState):
    return {
        **state,

        "intent": None,
        "active_flow": None,

        "appointment_id": None,
        "specialty": None,
        "referral_id": None,
        "form17_id": None,

        "available_slots": None,
        "selected_slot": None,

        "available_appointments": None,
        "selected_appointment_id": None,

        "pending_action": None,
        "pending_data": None,

        "tool_result": None,
        "answer": None,

        "waiting_for_specialty": False,
        "waiting_for_time_selection": False,
        "waiting_for_confirmation": False,
        "waiting_for_appointment_id": False,
        "waiting_for_referral_id": False,
        "waiting_for_form17_id": False,
        "waiting_for_appointment_selection": False,

        "needs_human": False,
    }


def detect_explicit_new_flow(text: str):
    text = text.lower()

    if (
        "לבטל תור" in text
        or "ביטול תור" in text
        or "cancel appointment" in text
    ):
        return "cancel_appointment"

    if (
        "לקבוע תור" in text
        or "קביעת תור" in text
        or "book appointment" in text
    ):
        return "book_appointment"

    if (
        "הפניה" in text
        or "referral" in text
    ):
        return "referral_status"

    if (
        "טופס 17" in text
        or "form 17" in text
    ):
        return "form17_status"

    if (
        "מענה אנושי" in text
        or "נציג" in text
        or "מזכירה" in text
        or "לדבר עם" in text
        or "speak" in text
        or "human" in text
        or "representative" in text
    ):
        return "human_escalation"

    return None


def detect_language(text: str) -> str:
    hebrew_chars = "אבגדהוזחטיכלמנסעפצקרשתךםןףץ"
    return "hebrew" if any(char in hebrew_chars for char in text) else "english"


def build_history_text(state, max_messages: int = 6) -> str:
    messages = state.get("messages", [])
    recent_messages = messages[-max_messages:]
    lines = []
    for message in recent_messages:
        role = message.get("role", "user")
        content = message.get("content", "")
        lines.append(f"{role}: {content}")
    return "\n".join(lines)


def extract_first_number(text: str):
    match = re.search(r"\d+", text)
    return match.group() if match else None


def extract_form17_id(text: str):
    numbers = re.findall(r"\d+", text)
    for number in numbers:
        if number != "17":
            return number
    return None


def should_reset_by_text(text: str) -> bool:
    text = text.lower()
    reset_keywords = [
        "עזוב",
        "תתחיל מחדש",
        "שיחה חדשה",
        "לא משנה",
        "שאלה אחרת",
        "restart",
        "start over",
        "new question",
        "never mind",
        "אני רוצה לצאת",
        "לצאת מהתהליך",
        "אני רוצה להתחיל מחדש",
        "אני רוצה להתחיל שיחה חדשה",
        "stop",
        "exit",
        "cancel flow",
    ]
    return any(keyword in text for keyword in reset_keywords)


def normalize_confirmation_text(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"(.)\1{2,}", r"\1", text)
    return text


def quick_confirmation_check(text: str):
    text = normalize_confirmation_text(text)

    reject_words = [
        "לא", "no", "nope", "cancel", "reject", "בטל", "תבטל", "לא לאשר",
    ]
    confirm_words = [
        "כן", "כה", "סבבה", "אוקי", "אוקיי", "מאשר", "מאשרת",
        "תאשר", "תאשרי", "יאללה", "yes", "yep", "ok", "okay", "approve", "confirm",
    ]

    if any(word in text for word in reject_words):
        return "reject"
    if any(word in text for word in confirm_words):
        return "confirm"
    return None


def detect_confirmation(text: str):
    quick_result = quick_confirmation_check(text)
    if quick_result:
        return quick_result
    return ai_confirmation_check(text)


def add_log(state, message: str):
    logs = state.get("logs", [])
    timestamp = datetime.now().strftime("%H:%M:%S")
    return logs + [f"[{timestamp}] {message}"]


def extract_specialty(text: str):
    text = text.lower()
    specialty_map = {
        "לב": "cardiology",
        "קרדיולוג": "cardiology",
        "קרדיולוגיה": "cardiology",
        "cardiology": "cardiology",
        "אורתופד": "orthopedics",
        "אורטופד": "orthopedics",
        "orthopedics": "orthopedics",
        "עור": "dermatology",
        "dermatology": "dermatology",
        "משפחה": "family",
        "family": "family",
        "ילדים": "children",
        "children": "children",
    }
    for keyword, value in specialty_map.items():
        if keyword in text:
            return value
    return None


def build_classifier_history(state, max_messages=4):
    messages = state.get("messages", [])
    if not messages:
        return ""

    # כלול גם user וגם assistant כדי לתת הקשר מלא לקלאסיפייר
    recent = messages[-(max_messages * 2):]

    lines = []
    for msg in recent:
        role = msg.get("role", "")
        content = msg.get("content", "").strip()
        if content:
            if role == "user":
                lines.append(f"User: {content}")
            elif role == "assistant":
                lines.append(f"Assistant: {content}")

    return "\n".join(lines)