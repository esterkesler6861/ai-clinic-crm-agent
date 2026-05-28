from typing import Optional, Literal, Any
from pydantic import BaseModel, Field


class IntentEntities(BaseModel):
    city: Optional[str] = None
    specialty: Optional[str] = None
    date: Optional[str] = None
    time_of_day: Optional[str] = None
    service: Optional[str] = None
    appointment_id: Optional[str] = None
    referral_id: Optional[str] = None
    form17_id: Optional[str] = None


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
        "knowledge_request",
    ]

    confidence: float
    needs_clarification: bool
    missing_fields: list[str]
    reason: str

    topic: Optional[str] = None
    entities: IntentEntities = Field(default_factory=IntentEntities)

    is_followup: bool = False
    resolved_user_input: Optional[str] = None

    user_sentiment: Literal[
        "neutral",
        "angry",
        "happy",
        "confused",
        "stressed",
    ] = "neutral"

    urgency: Literal[
        "low",
        "normal",
        "high",
    ] = "normal"

    language: Literal[
        "he",
        "en",
        "mixed",
    ] = "he"


class FlowDecision(BaseModel):
    continue_current_flow: bool
    reason: str


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