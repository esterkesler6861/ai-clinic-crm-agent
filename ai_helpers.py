from models import model
from prompts import (
    format_confirmation_classifier_prompt,
    format_slot_resolution_prompt,
)


def ai_confirmation_check(text: str):
    result = model.invoke(format_confirmation_classifier_prompt(text=text))

    value = result.content.strip().lower()
    return value if value in {"confirm", "reject", "unclear"} else "unclear"


def resolve_slot_with_ai(
    user_text: str,
    available_slots: list[str],
    history_text: str = "",
):
    response = model.invoke(
        format_slot_resolution_prompt(
            available_slots=available_slots,
            history_text=history_text,
            user_text=user_text,
        )
    )


    value = response.content.strip()

    if value in available_slots:
        return value

    if value == "show_options":
        return "show_options"

    return "unclear"