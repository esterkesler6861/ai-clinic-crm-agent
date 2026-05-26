from typing import Optional, Literal
from pydantic import BaseModel


class IntentResult(BaseModel):
    intent: Literal[
        "book_appointment",
        "cancel_appointment",
        "referral_status",
        "form17_status",
        "human_escalation",
        "general_feedback",
        "unknown",
        "unsupported_topic",
    ]
    confidence: float
    needs_clarification: bool
    missing_fields: list[str]
    reason: str


class FlowDecision(BaseModel):
    continue_current_flow: bool
    reason: str


from pydantic import BaseModel
from typing import Optional, Any


class ChatRequest(BaseModel):
    message: str
    state: Optional[dict[str, Any]] = None
    thread_id: Optional[str] = "demo-thread"


class ChatResponse(BaseModel):
    answer: str
    state: dict[str, Any]

class ClassificationEvaluation(BaseModel):
    decision_valid: bool
    suggested_intent: str | None = None
    evaluation_reason: str
