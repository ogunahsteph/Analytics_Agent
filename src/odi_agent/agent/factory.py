# """Assemble the model, instructions, tools, and memory."""

# from langchain.agents import create_agent

# from odi_agent.models import create_brain
# from odi_agent.agent.prompts import build_system_prompt
# from odi_agent.state.checkpoints import create_checkpointer
# from odi_agent.tools.registry import get_tools


# def build_agent():
#     return create_agent(
#         model=create_brain(),
#         tools=get_tools(),
#         system_prompt=build_system_prompt(),
#         checkpointer=create_checkpointer(),
#     )

"""Assemble the model, instructions, tools, and memory."""

from langchain.agents import create_agent
from langchain.tools import tool

from odi_agent.models import create_brain
from odi_agent.agent.context_loader import load_table_context
from odi_agent.agent.prompts import build_system_prompt
from odi_agent.state.checkpoints import create_checkpointer
from odi_agent.tools.registry import get_tools


@tool
def get_table_context(table_names: list[str]) -> str:
    """Load full business definitions for tables listed in the catalogue.

    Supply exact YAML table names, not BigQuery table IDs.
    Request all tables needed for the analysis together, including lookups.
    Definitions include columns, deduplication, joins, and time rules.
    """
    try:
        # NEW: Read only the requested definitions.
        # This reads local YAML files; it does not query BigQuery.
        return load_table_context(table_names=table_names)
    except (ValueError, FileNotFoundError) as exc:
        # Return a readable error so the agent can correct the table names.
        return f"Could not load table context: {exc}"


def build_agent():
    # NEW: Keep existing analytical tools and add context retrieval.
    # Future tables become discoverable through their YAML catalogue entries.
    tools = [
        *get_tools(),
        get_table_context,
    ]

    return create_agent(
        model=create_brain(),
        tools=tools,
        system_prompt=build_system_prompt(),
        checkpointer=create_checkpointer(),
    )