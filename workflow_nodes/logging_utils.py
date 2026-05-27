import logging

from graph_state import ClinicCRMState
from utils import add_log

# Use a stable logger name to preserve legacy logging behavior from `nodes.py`.
logger = logging.getLogger("nodes")


def with_log(state: ClinicCRMState, message: str):
    logger.info(message)
    return {
        **state,
        "logs": add_log(state, message),
    }
