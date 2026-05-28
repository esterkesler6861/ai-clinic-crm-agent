"""Legacy nodes facade.

The graph builds nodes via:
    from nodes import *

To keep that stable while refactoring, this module re-exports node functions
from the modular implementation under `workflow_nodes/`.

No behavior is intended to change here.
"""
from workflow_nodes.knowledge import knowledge_request_node
from workflow_nodes.logging_utils import with_log

from workflow_nodes.context_guard import context_guard_node
from workflow_nodes.intent_classification import (
    classify_intent_node,
    evaluate_classification_node,
    route_after_classification,
    route_by_intent,
)
from workflow_nodes.appointment_booking import (
    book_appointment_node,
    select_appointment_slot_node,
)
from workflow_nodes.appointment_cancellation import (
    cancel_appointment_node,
    select_appointment_to_cancel_node,
)
from workflow_nodes.statuses import form17_status_node, referral_status_node
from workflow_nodes.commons import (
    cancel_confirmation_node,
    confirm_action_node,
    general_feedback_node,
    human_escalation_node,
    unknown_node,
    unsupported_topic_node,
)
from workflow_nodes.response_generation import generate_response_node
from workflow_nodes.semantic_resolver import semantic_resolver_node

from workflow_nodes.conversation_frame import conversation_frame_node
from workflow_nodes.message_history import update_message_history_node

__all__ = [
    # Shared helpers
    "with_log",
    # Routing / classification
    "context_guard_node",
    "classify_intent_node",
    "route_after_classification",
    "evaluate_classification_node",
    "route_by_intent",
    # Appointment booking
    "book_appointment_node",
    "select_appointment_slot_node",
    # Appointment cancellation
    "cancel_appointment_node",
    "select_appointment_to_cancel_node",
    "confirm_action_node",
    "cancel_confirmation_node",
    # Status checks
    "referral_status_node",
    "form17_status_node",
    # Misc / fallbacks
    "human_escalation_node",
    "general_feedback_node",
    "unsupported_topic_node",
    "unknown_node",
    # Response
    "generate_response_node",
    # Knowledge
    "knowledge_request_node",
    "semantic_resolver_node",
    "conversation_frame_node",
    # Message history
    "update_message_history_node",
]