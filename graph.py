from langgraph.checkpoint.memory import InMemorySaver
from dotenv import load_dotenv
from langgraph.graph import StateGraph, START, END

from nodes import *
from graph_state import ClinicCRMState

import logging

logger = logging.getLogger(__name__)

load_dotenv()


graph_builder = StateGraph(ClinicCRMState)
checkpointer = InMemorySaver()

# Nodes
graph_builder.add_node("context_guard", context_guard_node)
graph_builder.add_node("classify_intent", classify_intent_node)
graph_builder.add_node("evaluate_classification", evaluate_classification_node)

graph_builder.add_node("book_appointment", book_appointment_node)
graph_builder.add_node("select_appointment_slot", select_appointment_slot_node)
graph_builder.add_node("confirm_action", confirm_action_node)
graph_builder.add_node("cancel_confirmation", cancel_confirmation_node)

graph_builder.add_node("cancel_appointment", cancel_appointment_node)
graph_builder.add_node("select_appointment_to_cancel", select_appointment_to_cancel_node)

graph_builder.add_node("referral_status", referral_status_node)
graph_builder.add_node("form17_status", form17_status_node)
graph_builder.add_node("human_escalation", human_escalation_node)

graph_builder.add_node("general_feedback", general_feedback_node)
graph_builder.add_node("unsupported_topic", unsupported_topic_node)
graph_builder.add_node("unknown", unknown_node)

graph_builder.add_node("knowledge_request", knowledge_request_node)
graph_builder.add_node("generate_response", generate_response_node)
graph_builder.add_node("update_message_history", update_message_history_node)

# Edges
graph_builder.add_edge(START, "context_guard")
graph_builder.add_edge("context_guard", "classify_intent")

graph_builder.add_conditional_edges(
    "classify_intent",
    route_after_classification,
)

graph_builder.add_conditional_edges(
    "evaluate_classification",
    route_by_intent,
)

graph_builder.add_edge("book_appointment", "generate_response")
graph_builder.add_edge("select_appointment_slot", "generate_response")
graph_builder.add_edge("confirm_action", "generate_response")
graph_builder.add_edge("cancel_confirmation", "generate_response")

graph_builder.add_edge("cancel_appointment", "generate_response")
graph_builder.add_edge("select_appointment_to_cancel", "generate_response")

graph_builder.add_edge("referral_status", "generate_response")
graph_builder.add_edge("form17_status", "generate_response")
graph_builder.add_edge("human_escalation", "generate_response")

graph_builder.add_edge("general_feedback", "generate_response")
graph_builder.add_edge("unsupported_topic", "generate_response")
graph_builder.add_edge("unknown", "generate_response")
graph_builder.add_edge("knowledge_request", "generate_response")

# generate_response -> update_message_history -> END
graph_builder.add_edge("generate_response", "update_message_history")
graph_builder.add_edge("update_message_history", END)

graph = graph_builder.compile(checkpointer=checkpointer)