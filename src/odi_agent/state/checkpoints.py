"""Conversation checkpoint storage."""

from langgraph.checkpoint.memory import InMemorySaver


def create_checkpointer():
    return InMemorySaver()