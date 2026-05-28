import logging

from graph_state import ClinicCRMState
from models import classification_evaluator_model, intent_model
from prompts import (
    format_classification_evaluator_prompt,
    format_intent_classifier_prompt,
)
from utils import (
    add_log,
    build_history_text,
    detect_confirmation,
    detect_explicit_new_flow,
    extract_first_number,
    build_classifier_history
)
from workflow_nodes.logging_utils import with_log

logger = logging.getLogger("nodes")


def route_by_intent(state: ClinicCRMState):
    intent = state.get("intent") or "unknown"
    logger.info(f"ROUTE BY INTENT | intent={intent}")
    return intent


def classify_intent_node(state: ClinicCRMState):
    state = with_log(
        state,
        f"NODE classify_intent_node | text={state.get('user_input')}",
    )

    if state.get("tool_result") == "flow_cancelled":
        return {
            **state,
            "intent": "general_feedback",
            "logs": add_log(state, "ROUTE | flow_cancelled"),
        }

    if state.get("tool_result") == "off_topic_during_flow":
        return {
            **state,
            "intent": "unknown",
            "logs": add_log(state, "ROUTE | off_topic_during_flow"),
        }

    explicit_flow = detect_explicit_new_flow(state["user_input"])

    text = (
        state.get("resolved_user_input")
        or state["user_input"]
    ).lower()

    number = extract_first_number(text)

    if state.get("last_completed_flow") == "form17_status" and number:
        return {
            **state,
            "intent": "form17_status",
            "decision_summary": "Deterministic continuation after previous Form 17 flow.",
            "logs": add_log(state, "LAST FLOW CONTINUATION | form17_status"),
        }

    if state.get("last_completed_flow") == "referral_status" and number:
        return {
            **state,
            "intent": "referral_status",
            "decision_summary": "Deterministic continuation after previous referral flow.",
            "logs": add_log(state, "LAST FLOW CONTINUATION | referral_status"),
        }

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
            "logs": add_log(state, "WAITING STATE ROUTE | select_appointment_to_cancel"),
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

    history_text = build_classifier_history(state)

    result = intent_model.invoke(
        format_intent_classifier_prompt(
            history_text=history_text,
            user_input=(
                state.get("resolved_user_input")
                or state["user_input"]
            ),
        )
    )

    entities = result.entities.model_dump()

    return {
        **state,

        "intent": result.intent,
        "topic": result.topic,
        "entities": entities,

        "resolved_user_input": (
            result.resolved_user_input
            or state["user_input"]
        ),

        "is_followup": result.is_followup,
        "user_sentiment": result.user_sentiment,
        "urgency": result.urgency,
        "language": result.language,

        "last_completed_flow": (
            state.get("last_completed_flow")
            if result.intent == "unknown"
            else None
        ),

        "active_flow": (
            result.intent
            if result.intent != "unknown"
            else None
        ),

        "classification_confidence": result.confidence,

        "decision_summary": (
            f"Classifier selected intent '{result.intent}' "
            f"with confidence {result.confidence}. "
            f"Reason: {result.reason}"
        ),

        "logs": add_log(
            state,
            f"INTENT CLASSIFIED | "
            f"intent={result.intent} | "
            f"confidence={result.confidence} | "
            f"needs_clarification={result.needs_clarification} | "
            f"missing_fields={result.missing_fields} | "
            f"followup={result.is_followup} | "
            f"entities={entities} | "
            f"sentiment={result.user_sentiment} | "
            f"urgency={result.urgency} | "
            f"language={result.language} | "
            f"reason={result.reason}",
        ),
    }


def route_after_classification(state: ClinicCRMState):
    if state.get("tool_result") == "off_topic_during_flow":
        logger.info("ROUTE AFTER CLASSIFICATION | off_topic_during_flow -> unknown")
        return "unknown"

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
        "מוקד",
        "רפואה דחופה",
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

    result = classification_evaluator_model.invoke(
        format_classification_evaluator_prompt(
            user_input=state.get("user_input"),
            intent=state.get("intent"),
        )
    )

    state = with_log(
        state,
        f"EVALUATION RESULT | valid={result.decision_valid} | "
        f"suggested={result.suggested_intent} | "
        f"reason={result.evaluation_reason}",
    )

    if result.decision_valid:
        previous_summary = state.get("decision_summary") or ""

        return {
            **state,
            "decision_summary": (
                previous_summary
                + " Evaluator approved the classification. "
                + f"Reason: {result.evaluation_reason}"
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


__all__ = [
    "route_by_intent",
    "classify_intent_node",
    "route_after_classification",
    "evaluate_classification_node",
]