import logging

from graph_state import ClinicCRMState
from models import intent_model, model, flow_decision_model,classification_evaluator_model
from tools import (
    get_available_appointments,
    cancel_appointment,
    get_patient_appointments,
    get_form17_status,
    get_referral_status,
    book_appointment,
)
from utils import (
    reset_state,
    detect_language,
    detect_explicit_new_flow,
    detect_confirmation,
    extract_first_number,
    extract_specialty,
    should_reset_by_text,
    add_log,
    build_history_text,
    extract_form17_id
)
from ai_helpers import resolve_slot_with_ai
from prompts import (
    format_context_guard_prompt,
    format_general_feedback_prompt,
    format_intent_classifier_prompt,
    format_workflow_response_prompt,
)

logger = logging.getLogger(__name__)


def with_log(state: ClinicCRMState, message: str):
    logger.info(message)
    return {
        **state,
        "logs": add_log(state, message),
    }


def route_by_intent(state: ClinicCRMState):
    intent = state.get("intent") or "unknown"
    logger.info(f"ROUTE BY INTENT | intent={intent}")
    return intent


def context_guard_node(state: ClinicCRMState):

    state = with_log(
        state,
        f"NODE context_guard_node | text={state.get('user_input')} | active_flow={state.get('active_flow')}",
    )

    history_text = build_history_text(state)
    text = state["user_input"]
    explicit_new_flow = detect_explicit_new_flow(text)

    if explicit_new_flow and explicit_new_flow != state.get("active_flow"):
        state = with_log(
            state,
            f"EXPLICIT FLOW SWITCH | from={state.get('active_flow')} | to={explicit_new_flow}",
        )

        new_state = reset_state(state)

        return {
            **new_state,
            "user_input": text,
            "logs": add_log(
                new_state,
                f"STATE RESET FOR NEW FLOW | flow={explicit_new_flow}",
            ),
        }

    if should_reset_by_text(text):
        state = with_log(state, "RESET REQUEST DETECTED")
        new_state = reset_state(state)

        return {
        **new_state,
        "intent": "general_feedback",
        "answer": "בסדר, יצאתי מהתהליך. אפשר להתחיל פעולה חדשה.",
        "logs": add_log(new_state, "STATE RESET BY USER TEXT"),
    }

    has_active_waiting = (
        state.get("waiting_for_specialty", False)
        or state.get("waiting_for_time_selection", False)
        or state.get("waiting_for_confirmation", False)
        or state.get("waiting_for_appointment_id", False)
        or state.get("waiting_for_referral_id", False)
        or state.get("waiting_for_form17_id", False)
        or state.get("waiting_for_appointment_selection", False)
    )

    if not has_active_waiting:
        return with_log(state, "NO ACTIVE WAITING STATE")

    # Deterministic shortcut:
    # If the graph is waiting for a specialty and the user gave a known specialty,
    # continue the current flow without asking the AI context guard.
    if state.get("waiting_for_specialty", False):
        specialty = extract_specialty(text)

        if specialty:
            return with_log(
                state,
                f"CONTEXT GUARD | specialty detected={specialty}",
            )
    if state.get("waiting_for_time_selection", False):
        return with_log(
            state,
            "CONTEXT GUARD | waiting_for_time_selection - continue current flow",
        )
    result = flow_decision_model.invoke(f"""
You are a context validator for a clinic CRM assistant.

The assistant may be waiting for a missing detail from the user.

Decide whether the new user message continues the current active workflow
or starts a different topic.

Current active flow: {state.get("active_flow")}

Waiting flags:
waiting_for_specialty: {state.get("waiting_for_specialty", False)}
waiting_for_time_selection: {state.get("waiting_for_time_selection", False)}
waiting_for_confirmation: {state.get("waiting_for_confirmation", False)}
waiting_for_appointment_id: {state.get("waiting_for_appointment_id", False)}
waiting_for_referral_id: {state.get("waiting_for_referral_id", False)}
waiting_for_form17_id: {state.get("waiting_for_form17_id", False)}
waiting_for_appointment_selection: {state.get("waiting_for_appointment_selection", False)}

Available slots: {state.get("available_slots")}
Available appointments: {state.get("available_appointments")}
Selected slot: {state.get("selected_slot")}
Pending action: {state.get("pending_action")}

New user message:
{text}

Conversation history:
{history_text}

Return continue_current_flow=true only if the message appears to answer the missing detail.
""")

    state = with_log(
        state,
        f"CONTEXT DECISION | continue_current_flow={result.continue_current_flow}",
    )

    if result.continue_current_flow:
        return state

    new_state = reset_state(state)

    return {
        **new_state,
        "logs": add_log(new_state, "CONTEXT GUARD RESETTING STATE"),
    }


def classify_intent_node(state: ClinicCRMState):
    state = with_log(
        state,
        f"NODE classify_intent_node | text={state.get('user_input')}",
    )
    explicit_flow = detect_explicit_new_flow(state["user_input"])

    if explicit_flow == "human_escalation":
        return {
        **state,
        "intent": "human_escalation",
        "active_flow": None,
        "decision_summary": "Deterministic override detected human escalation request.",
        "logs": add_log(state, "OVERRIDE ROUTE | human_escalation"),
        }
    if state.get("waiting_for_appointment_selection", False):
        return {
            **state,
            "intent": "select_appointment_to_cancel",
            "logs": add_log(
                state, "WAITING STATE ROUTE | select_appointment_to_cancel"
            ),
        }

    if state.get("waiting_for_confirmation", False):
        confirmation = detect_confirmation(state["user_input"])

        state = with_log(
            state,
            f"CONFIRMATION DETECTED | result={confirmation}",
        )

        if confirmation == "confirm":
            return {
                **state,
                "intent": "confirm_action",
                "logs": add_log(state, "ROUTE | confirm_action"),
            }

        if confirmation == "reject":
            return {
                **state,
                "intent": "cancel_confirmation",
                "logs": add_log(state, "ROUTE | cancel_confirmation"),
            }

        return {
            **state,
            "intent": "unknown",
            "logs": add_log(state, "CONFIRMATION UNCLEAR | route unknown"),
        }

    if state.get("waiting_for_time_selection", False):
        return {
            **state,
            "intent": "select_appointment_slot",
            "logs": add_log(state, "WAITING STATE ROUTE | select_appointment_slot"),
        }

    if state.get("waiting_for_specialty", False):
        return {
            **state,
            "intent": "book_appointment",
            "logs": add_log(state, "WAITING STATE ROUTE | book_appointment"),
        }

    if state.get("waiting_for_appointment_id", False):
        return {
            **state,
            "intent": "cancel_appointment",
            "logs": add_log(state, "WAITING STATE ROUTE | cancel_appointment"),
        }

    if state.get("waiting_for_referral_id", False):
        return {
            **state,
            "intent": "referral_status",
            "logs": add_log(state, "WAITING STATE ROUTE | referral_status"),
        }

    if state.get("waiting_for_form17_id", False):
        return {
            **state,
            "intent": "form17_status",
            "logs": add_log(state, "WAITING STATE ROUTE | form17_status"),
        }
    history_text = build_history_text(state)
    result = intent_model.invoke(f"""
You are an intent classifier for a clinic CRM assistant.

The assistant is administrative only.
It does not provide medical diagnosis, medical advice, or treatment instructions.

Classify the user message into exactly one intent:

- book_appointment: scheduling, asking for available appointments, doctor availability
- cancel_appointment: cancelling an appointment
- referral_status: checking referral status
- form17_status: checking Form 17 / התחייבות status
- human_escalation: urgent, sensitive, angry, unsafe, or requires human staff
- unsupported_topic: clearly unrelated topics that the clinic CRM assistant should not answer, such as weather, news, homework, general knowledge, jokes, or non-clinic questions
- unknown: unclear clinic-related or ambiguous operational request

Examples:
- "מה מזג האוויר" => unsupported_topic
- "ספר לי בדיחה" => unsupported_topic
- "יש משהו" => unknown
- "תור" => book_appointment
- "תודה" => general_feedback

Return a structured result with:
- intent
- confidence: number between 0 and 1
- needs_clarification: true if the request is relevant but missing required information
- missing_fields: list of missing fields, for example ["specialty"]
- reason: short explanation

Booking classification rules:
- The classifier should identify only the user's general intent, not validate specific specialties.
- Specialty validation happens later in the workflow, not in the classifier.
- If the user asks for an appointment, scheduling, availability, doctor/service, or writes a short phrase that likely means they need a clinic appointment, classify as book_appointment.
- If the message is short or incomplete, use medium confidence, not high confidence.
- Do not return high confidence for unknown unless the message is clearly unrelated to clinic administration.

Examples:
- "צריכה ילדים" => intent=book_appointment, confidence=0.6, needs_clarification=true
- "צריכה קרדיולוג" => intent=book_appointment, confidence=0.7, needs_clarification=true
- "אני רוצה תור" => intent=book_appointment, confidence=0.9, needs_clarification=true, missing_fields=["specialty"]
- "אני רוצה תור לילדים" => intent=book_appointment, confidence=0.95, needs_clarification=false
- "מה מזג האוויר" => intent=unknown, confidence=0.95

For book_appointment:
- Required missing field is only specialty.
- Do not mark date or time as missing, because available slots are selected later from the system.

Do not classify unclear operational requests as general_feedback.
Examples:
- "תודה" => general_feedback
- "מעולה עזרת לי" => general_feedback
- "היי" => general_feedback
- "יש משהו" => unknown
- "תור" => book_appointment
- "להיום" => unknown unless there is active workflow context

Conversation history:
{history_text}
User message:
{state["user_input"]}
""")
    
    return {
        **state,
        "intent": result.intent,
        "active_flow": result.intent if result.intent != "unknown" else None,
        "classification_confidence": result.confidence,
        "decision_summary": (
    f"Classifier selected intent '{result.intent}' "
    f"with confidence {result.confidence}. "
    f"Reason: {result.reason}"
),
        "logs": add_log(
            state,
            
            f"INTENT CLASSIFIED | intent={result.intent} | confidence={result.confidence} | needs_clarification={result.needs_clarification} | missing_fields={result.missing_fields} | reason={result.reason}",
        ),
    }
def route_after_classification(state: ClinicCRMState):
    intent = state.get("intent") or "unknown"
    confidence = state.get("classification_confidence", 1)
    text = (state.get("user_input") or "").lower()

    logger.info(
        f"ROUTE AFTER CLASSIFICATION | intent={intent} | confidence={confidence}"
    )

    clinic_keywords = [
        "תור",
        "לקבוע",
        "לבטל",
        "הפניה",
        "טופס 17",
        "התחייבות",
        "מזכירה",
        "נציג",
        "מענה אנושי",
        "רופא",
        "מרפאה",
    ]

    suspicious = False
    reasons = []

    if confidence < 0.65:
        suspicious = True
        reasons.append("very_low_confidence")

    if intent == "unknown" and any(word in text for word in clinic_keywords):
        suspicious = True
        reasons.append("unknown_but_clinic_related")

    if intent == "unsupported_topic" and any(word in text for word in clinic_keywords):
        suspicious = True
        reasons.append("unsupported_but_clinic_related")

    if intent == "general_feedback" and any(word in text for word in clinic_keywords):
        suspicious = True
        reasons.append("feedback_but_workflow_related")

    if suspicious:
        logger.info(
            f"SUSPICIOUS CLASSIFICATION -> evaluate_classification | reasons={reasons}"
        )
        return "evaluate_classification"

    logger.info(f"CLASSIFICATION OK -> direct route | intent={intent}")
    return intent


def evaluate_classification_node(state: ClinicCRMState):

    state = with_log(
        state,
        f"NODE evaluate_classification_node | intent={state.get('intent')}",
    )

    result = classification_evaluator_model.invoke(f"""
You are an evaluator for a clinic CRM AI routing system.

Your task:
Review whether the intent classification is logically consistent.

User message:
{state.get("user_input")}

Classifier result:
intent={state.get("intent")}

Rules:
- Reject classifications that clearly contradict the user message.
- Reject high-confidence unknown classifications for partially clinic-related requests.
- Approve short ambiguous booking-related requests if they reasonably suggest appointment intent.
- Do not invent new workflows.
- suggested_intent should only be used if the classifier is clearly wrong.

Examples:
- "צריכה ילדים" + unknown => invalid, suggest book_appointment
- "מה מזג האוויר" + unsupported_topic => valid
- "תודה רבה" + general_feedback => valid
- "אני רוצה לבטל תור" + cancel_appointment => valid

Return:
- decision_valid
- suggested_intent
- evaluation_reason
""")

    state = with_log(
        state,
        f"EVALUATION RESULT | valid={result.decision_valid} | suggested={result.suggested_intent} | reason={result.evaluation_reason}",
    )

    if result.decision_valid:
        previous_summary = state.get("decision_summary") or ""

        return {
        **state,
        "decision_summary": (
            previous_summary
            + f" Evaluator approved the classification. "
              f"Reason: {result.evaluation_reason}"
        ),
    }
        
    if result.suggested_intent:
        
      previous_summary = state.get("decision_summary") or ""
      return {
            **state,
            "intent": result.suggested_intent,
            "decision_summary": (
            previous_summary
            + f" Evaluator rejected the original classification "
              f"and changed intent to '{result.suggested_intent}'. "
              f"Reason: {result.evaluation_reason}"
        ),
            "logs": add_log(
                state,
                f"EVALUATOR CHANGED INTENT | new_intent={result.suggested_intent}",
            ),
        }

    return {
        **state,
        "intent": "unknown",
        "logs": add_log(
            state,
            "EVALUATOR REJECTED CLASSIFICATION | fallback=unknown",
        ),
    }
    

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
            "logs": add_log(state, "לא נמצאה התחייבות עם המספר שלחת. אנא וודא שהמספר שהזנת נכון ונסה שוב."), 
        }

    tool_result = get_form17_status(form17_id)

    return {
        **state,
        "form17_id": form17_id,
        "active_flow": None,
        "waiting_for_form17_id": False,
        "tool_result": tool_result,
        "logs": add_log(state, f"FORM17 STATUS RESULT | result={tool_result}"),
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
    if state.get("intent") == "general_feedback":
        response = model.invoke(f"""
You are an AI CRM assistant for a healthcare clinic secretary.

The user wrote a greeting, thanks, positive feedback, or polite small talk.

Answer warmly, shortly, and professionally.
Do not start a workflow.
Do not ask for appointment date, time, ID, phone, or medical details.
Answer in the user's language.

User message:
{state.get("user_input")}
""")

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

    response = model.invoke(f"""
You are an AI CRM assistant for a healthcare clinic secretary.

Your role is administrative only.

Critical workflow rules:
- Never invent missing fields.
- Do not ask for name, ID number, birth date, phone, email, or preferred period.
- The user is already authenticated in this MVP.
- Ask only for information that the current state is waiting for.
- If waiting_for_specialty is true, ask only for specialty.
- If waiting_for_time_selection is true, ask only the user to choose one of the shown appointment slots.
- If waiting_for_appointment_selection is true, ask only the user to choose one of the shown appointments.
- If waiting_for_confirmation is true, ask only whether the user confirms.
- Never invent additional workflow steps.
- Never expose internal system details, intents, flags, or workflow logic.
- Answer in the user's language.
- Be short, practical, warm, and professional.

Conversation history:
{history_text}
User language: {language}
User message: {state.get("user_input")}
Intent: {state.get("intent")}

State:
active_flow: {state.get("active_flow")}
pending_action: {state.get("pending_action")}
pending_data: {state.get("pending_data")}

specialty: {state.get("specialty")}
available_slots: {state.get("available_slots")}
selected_slot: {state.get("selected_slot")}

available_appointments: {state.get("available_appointments")}
selected_appointment_id: {state.get("selected_appointment_id")}

appointment_id: {state.get("appointment_id")}
referral_id: {state.get("referral_id")}
form17_id: {state.get("form17_id")}

waiting_for_specialty: {state.get("waiting_for_specialty", False)}
waiting_for_time_selection: {state.get("waiting_for_time_selection", False)}
waiting_for_appointment_selection: {state.get("waiting_for_appointment_selection", False)}
waiting_for_confirmation: {state.get("waiting_for_confirmation", False)}
waiting_for_appointment_id: {state.get("waiting_for_appointment_id", False)}
waiting_for_referral_id: {state.get("waiting_for_referral_id", False)}
waiting_for_form17_id: {state.get("waiting_for_form17_id", False)}
needs_human: {state.get("needs_human", False)}

Generate the final answer to the user.
""")

    return {
        **state,
        "answer": response.content,
        "logs": add_log(state, "AI WORKFLOW RESPONSE GENERATED"),
    }
