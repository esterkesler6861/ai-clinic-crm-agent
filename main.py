try:
    import certifi_win32
except ImportError:
    pass


from dotenv import load_dotenv
from logger_config import setup_logging

load_dotenv()
setup_logging()
import logging
import os
print("OPENAI KEY EXISTS:", bool(os.getenv("OPENAI_API_KEY")))

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from graph import graph
from pydantic import BaseModel
from typing import Any
from routing_tests import run_routing_tests
from schemas import ChatRequest, ChatResponse

logger = logging.getLogger(__name__)

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")


def create_initial_state(user_input: str):
    return {
        "user_input": user_input,
        # REQUIRED FOR LANGGRAPH CHECKPOINTER
        "thread_id": "demo-thread",
        "intent": None,
        "active_flow": None,
        "patient_id": "demo-patient-123",
        "appointment_id": None,
        "specialty": None,
        "referral_id": None,
        "form17_id": None,
        "available_slots": None,
        "selected_slot": None,
        "available_appointments": None,
        "selected_appointment_id": None,
        "pending_action": None,
        "pending_data": None,
        "tool_result": None,
        "answer": None,
        "waiting_for_specialty": False,
        "waiting_for_time_selection": False,
        "waiting_for_confirmation": False,
        "waiting_for_appointment_id": False,
        "waiting_for_referral_id": False,
        "waiting_for_form17_id": False,
        "waiting_for_appointment_selection": False,
        "needs_human": False,
        "logs": [],
        "messages": [],
        "last_completed_flow": None,
    }


def normalize_state(state: dict, user_input: str):
    base_state = create_initial_state(user_input)

    base_state.update(state or {})

    base_state["user_input"] = user_input
    base_state["answer"] = None
    base_state["tool_result"] = None
    base_state["messages"] = (state.get("messages") or [])[-10:]
    return base_state


@app.get("/")
def home():
    logger.info("Serving static/index.html")
    return FileResponse("static/index.html")


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    try:
        logger.info(f"CHAT REQUEST | message={request.message}")

        state = {
            "user_input": request.message,
            "messages": [
                {
                    "role": "user",
                    "content": request.message,
                }
            ],
        }

        result = graph.invoke(
            state,
            config={
                "configurable": {
                    "thread_id": request.thread_id
                }
            },
        )

        messages = result.get("messages") or []

        messages.append({
            "role": "assistant",
            "content": result.get("answer") or "",
        })

        result["messages"] = messages[-10:]

        return {
            "answer": result.get("answer") or "לא הצלחתי להפיק תשובה.",
            "state": result,
        }

    except Exception as e:
        logger.exception("CHAT REQUEST FAILED")

        fallback_state = create_initial_state(request.message)
        fallback_state["logs"] = [f"ERROR | {str(e)}"]

        return {
            "answer": f"שגיאה: {str(e)}",
            "state": fallback_state,
        }

class RoutingTestCase(BaseModel):
    input: str
    expected_intent: str


class RoutingTestRequest(BaseModel):
    tests: list[RoutingTestCase] | None = None


@app.get("/routing-dashboard")
def routing_dashboard():
    return FileResponse("static/routing_dashboard.html")


@app.post("/routing-tests")
def routing_tests(request: RoutingTestRequest):
    tests = [test.model_dump() for test in request.tests] if request.tests else None
    return run_routing_tests(tests)