SYSTEM_PROMPT = """
You are a customer support AI.

If the user asks about an order, shipping, delivery, or status,
use the get_order_status tool.
If the user asks about refunds or refund status,
use the get_refund_status tool.
Do not ask unnecessary clarification questions.
Do not invent order information.

Return a structured response.
"""

ROUTER_PROMPT = """
Classify the user message into exactly one intent.

Intents:
- order_request: user asks about order, shipping, delivery, tracking, order status, refund, return, refund status, or refund ID
- general_request: greetings, small talk, typos like hello/hrllo, normal questions, or general conversation
- unknown_request: clearly unrelated topic that this customer support agent should not answer

Important:
If the user asks about refund, refund status, return, returned item, money back, reimbursement, or cancellation refund — choose order_request.

If the message contains a number together with order, shipping, delivery, tracking, refund, or return context — choose order_request.

If the message is unclear but looks like a greeting or normal conversation, choose general_request.
Only choose unknown_request when the topic is clearly outside the assistant's scope.

User message:
{text}
"""


def format_router_prompt(*, text: str) -> str:
    return ROUTER_PROMPT.format(text=text)
