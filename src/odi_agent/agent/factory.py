"""Assemble the model, instructions, tools, and memory."""

from langchain.agents import create_agent

from odi_agent.models import create_brain
from odi_agent.agent.prompts import build_system_prompt
from odi_agent.state.checkpoints import create_checkpointer
from odi_agent.tools.registry import get_tools


def build_agent():
    return create_agent(
        model=create_brain(),
        tools=get_tools(),
        system_prompt=build_system_prompt(),
        checkpointer=create_checkpointer(),
    )