from typing import Literal

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from pydantic import BaseModel

from prompts import format_router_prompt


class RouteResult(BaseModel):
    intent: Literal["order_request", "general_request", "unknown_request"]
    reason: str


load_dotenv()

router_model = ChatOpenAI(
    model="gpt-4.1-mini",
)

router = router_model.with_structured_output(RouteResult)


def route_user_message(text: str) -> RouteResult:
    return router.invoke(format_router_prompt(text=text))