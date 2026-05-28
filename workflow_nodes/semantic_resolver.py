from graph_state import ClinicCRMState
from workflow_nodes.logging_utils import with_log


def semantic_resolver_node(state: ClinicCRMState):

    return with_log(
        {
            **state,
            "resolved_user_input": state["user_input"],
            "is_followup": False,
        },
        "SEMANTIC RESOLVER | passthrough",
    )