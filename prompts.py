"""Backward-compatible prompt facade.

Historically this project kept all prompt strings in a single `prompts.py`.
As part of the nodes modularization, prompt templates were moved into dedicated
modules under `prompt_templates/`.

This file keeps the original import paths stable:
    from prompts import format_workflow_response_prompt
"""

from prompt_templates.clinic_crm import (  # noqa: F401
    CLASSIFICATION_EVALUATOR_PROMPT,
    CONFIRMATION_CLASSIFIER_PROMPT,
    CONTEXT_GUARD_PROMPT,
    GENERAL_FEEDBACK_PROMPT,
    INTENT_CLASSIFIER_PROMPT,
    SLOT_RESOLUTION_PROMPT,
    WORKFLOW_RESPONSE_PROMPT,
    format_classification_evaluator_prompt,
    format_confirmation_classifier_prompt,
    format_context_guard_prompt,
    format_general_feedback_prompt,
    format_intent_classifier_prompt,
    format_slot_resolution_prompt,
    format_workflow_response_prompt,
)
from prompt_templates.customer_support import (  # noqa: F401
    ROUTER_PROMPT,
    SYSTEM_PROMPT,
    format_router_prompt,
)

__all__ = [
    # Prompt constants
    "SYSTEM_PROMPT",
    "CONTEXT_GUARD_PROMPT",
    "INTENT_CLASSIFIER_PROMPT",
    "GENERAL_FEEDBACK_PROMPT",
    "WORKFLOW_RESPONSE_PROMPT",
    "CLASSIFICATION_EVALUATOR_PROMPT",
    "CONFIRMATION_CLASSIFIER_PROMPT",
    "SLOT_RESOLUTION_PROMPT",
    "ROUTER_PROMPT",
    # Formatter helpers
    "format_context_guard_prompt",
    "format_intent_classifier_prompt",
    "format_general_feedback_prompt",
    "format_workflow_response_prompt",
    "format_classification_evaluator_prompt",
    "format_confirmation_classifier_prompt",
    "format_slot_resolution_prompt",
    "format_router_prompt",
]

