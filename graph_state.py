from typing import Optional, Literal, Any
from typing_extensions import TypedDict


class ClinicCRMState(TypedDict):
    user_input: str
    messages: list[dict[str, str]]
    decision_summary: Optional[str]
    classification_confidence: Optional[float]
    intent: Optional[
        Literal[
            "book_appointment",
            "select_appointment_slot",
            "confirm_action",
            "cancel_confirmation",
            "cancel_appointment",
            "referral_status",
            "form17_status",
            "human_escalation",
            "unknown",
            "select_appointment_to_cancel",
            "general_feedback",
            "unsupported_topic"
        ]
    ]

    active_flow: Optional[str]

    # For this MVP we assume the patient is already authenticated.
    patient_id: Optional[str]

    appointment_id: Optional[str]
    specialty: Optional[str]
    referral_id: Optional[str]
    form17_id: Optional[str]

    available_slots: Optional[list]
    selected_slot: Optional[str]

    pending_action: Optional[str]
    pending_data: Optional[dict[str, Any]]

    tool_result: Optional[Any]
    answer: Optional[str]

    waiting_for_specialty: bool
    waiting_for_time_selection: bool
    waiting_for_confirmation: bool
    waiting_for_appointment_id: bool
    waiting_for_referral_id: bool
    waiting_for_form17_id: bool

    needs_human: bool
    available_appointments: Optional[list]
    selected_appointment_id: Optional[str]
    waiting_for_appointment_selection: bool
    logs: list[str]