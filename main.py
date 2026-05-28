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
from datetime import datetime

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from graph import graph
from routing_tests import run_routing_tests
from schemas import ChatRequest, ChatResponse

from pydantic import BaseModel

logger = logging.getLogger(__name__)

print("OPENAI KEY EXISTS:", bool(os.getenv("OPENAI_API_KEY")))

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")


def create_initial_state(user_input: str):
    return {
        "user_input": user_input,
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

        "current_datetime": None,
        "current_date": None,
        "current_time": None,
        "current_weekday": None,
        "timezone": None,

        "conversation_frame": None,
        "resolved_user_input": None,
        "is_followup": False,
    }


@app.get("/")
def home():
    logger.info("Serving static/index.html")
    return FileResponse("static/index.html")


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    try:
        logger.info(f"CHAT REQUEST | message={request.message}")

        now = datetime.now().astimezone()

        # חשוב:
        # לא מאפסים כאן את כל ה-state.
        # נותנים ל-LangGraph checkpointer לשמור את מצב השיחה לפי thread_id.
        state = {
            "user_input": request.message,
            "thread_id": request.thread_id or "demo-thread",
            "current_datetime": now.isoformat(),
            "current_date": now.strftime("%Y-%m-%d"),
            "current_time": now.strftime("%H:%M"),
            "current_weekday": now.strftime("%A"),
            "timezone": str(now.tzinfo),
        }

        result = graph.invoke(
            state,
            config={
                "configurable": {
                    "thread_id": request.thread_id or "demo-thread",
                }
            },
        )

        final_answer = (
            result.get("answer")
            or result.get("tool_result")
            or "לא התקבלה תשובה."
        )

        logger.info(f"FINAL ANSWER | {final_answer}")
        logger.info(f"FINAL INTENT | {result.get('intent')}")
        logger.info(f"FINAL ACTIVE FLOW | {result.get('active_flow')}")

        return {
            "answer": final_answer,
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
    tests = (
        [test.model_dump() for test in request.tests]
        if request.tests
        else None
    )

    return run_routing_tests(tests)