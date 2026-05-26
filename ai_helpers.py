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
    response = model.invoke(f"""
You resolve appointment slot selection.

Available slots:
{available_slots}

Conversation history:
{history_text}

User message:
{user_text}

Return exactly one of:
- an exact slot from Available slots
- show_options
- unclear

Rules:
- If the user says first/הראשון, return the first slot.
- If the user says second/השני, return the second slot.
- If the user mentions a day/date/time that matches one slot, return that exact slot.
- If the user asks for another option/more options/something else, return show_options.
- Never invent a slot.
- Return only the final value.
""")

    value = response.content.strip()

    if value in available_slots:
        return value

    if value == "show_options":
        return "show_options"

    return "unclear"