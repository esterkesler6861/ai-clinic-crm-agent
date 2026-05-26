import logging

logger = logging.getLogger(__name__)
def run_order_flow(agent, user_input: str, thread_id: str):
    logger.info(f"Running order flow | text={user_input}")
    result = agent.invoke(
        {
            "messages": [
                {"role": "user", "content": user_input}
            ]
        },
        config={
            "configurable": {
                "thread_id": thread_id
            }
        }
    )

    return result["structured_response"]