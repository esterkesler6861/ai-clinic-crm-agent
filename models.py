from langchain_openai import ChatOpenAI

from schemas import IntentResult, FlowDecision, ClassificationEvaluation


COMMON_CONFIG = {
    "model": "gpt-4.1-mini",
    "temperature": 0,
    "max_retries": 2,
    "timeout": 60,
}

model = ChatOpenAI(**COMMON_CONFIG)

intent_model = model.with_structured_output(IntentResult)

flow_decision_model = model.with_structured_output(FlowDecision)

classification_evaluator_model = model.with_structured_output(
    ClassificationEvaluation
)