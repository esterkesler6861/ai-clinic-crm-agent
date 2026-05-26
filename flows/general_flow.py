import logging

logger = logging.getLogger(__name__)
def run_general_flow(user_input: str):
    logger.info(f"Running general flow | text={user_input}")
    return f"General response: {user_input}"