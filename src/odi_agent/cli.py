# """Interactive terminal interface."""

# from uuid import uuid4

# from langgraph.errors import GraphRecursionError

# from odi_agent.agent.factory import build_agent


# def show_text(message):
#     """Display only the response text."""
#     if isinstance(message.content, str):
#         print(message.content)
#     else:
#         print("\n".join(
#             block["text"]
#             for block in message.content
#             if isinstance(block, dict) and block.get("type") == "text"
#         ))


# def main():
#     agent = build_agent()

#     config = {
#         "configurable": {"thread_id": uuid4().hex},
#         "recursion_limit": 12,
#     }

#     print("Odi Analytics Agent")
#     print("Ask a question, /new for a new conversation, or /exit to quit.")

#     while True:
#         try:
#             question = input("\nYou: ").strip()
#         except (EOFError, KeyboardInterrupt):
#             print("\nGoodbye.")
#             break

#         if not question:
#             continue

#         if question.lower() == "/exit":
#             break

#         if question.lower() == "/new":
#             config["configurable"]["thread_id"] = uuid4().hex
#             print("New conversation started.")
#             continue

#         try:
#             result = agent.invoke(
#                 {"messages": [{"role": "user", "content": question}]},
#                 config=config,
#             )

#             print("\nAgent:")
#             show_text(result["messages"][-1])

#         except GraphRecursionError:
#             print("Execution-step limit reached. Use /new before retrying.")

#         except Exception as exc:
#             print(f"Request failed: {exc}")


# if __name__ == "__main__":
#     main()
"""Interactive terminal interface with per-request token tracking."""

import json
from uuid import uuid4

# Collects reported token usage across the model calls in one request.
from langchain_core.callbacks import get_usage_metadata_callback
from langgraph.errors import GraphRecursionError

from odi_agent.agent.factory import build_agent


def show_text(message):
    """Display only the response text."""
    if isinstance(message.content, str):
        print(message.content)
    else:
        print("\n".join(
            block["text"]
            for block in message.content
            if isinstance(block, dict) and block.get("type") == "text"
        ))


def show_usage(usage):
    """Show reported usage, grouped by model, for this request."""
    metadata = usage.usage_metadata

    print("\n--- Model token usage for this request ---")

    # Missing metadata does not mean the request consumed zero tokens.
    if not metadata:
        print("Token usage was not reported by the model integration.")
        return

    # Details may include cached input and reasoning tokens.
    # These are breakdowns, not extra tokens to add to the totals.
    print(json.dumps(metadata, indent=2))

    input_tokens = sum(
        counts.get("input_tokens", 0)
        for counts in metadata.values()
    )
    output_tokens = sum(
        counts.get("output_tokens", 0)
        for counts in metadata.values()
    )

    print(f"Total input tokens:  {input_tokens:,}")
    print(f"Total output tokens: {output_tokens:,}")

    # We don't calculate dollars here: rates vary by model, caching,
    # and pricing tier. BigQuery query charges are separate.


def main():
    agent = build_agent()

    config = {
        "configurable": {"thread_id": uuid4().hex},
        "recursion_limit": 12,
    }

    print("Odi Analytics Agent")
    print("Ask a question, /new for a new conversation, or /exit to quit.")

    while True:
        try:
            question = input("\nYou: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye.")
            break

        if not question:
            continue

        if question.lower() == "/exit":
            break

        if question.lower() == "/new":
            config["configurable"]["thread_id"] = uuid4().hex
            print("New conversation started.")
            continue

        # A fresh collector for each question prevents previous
        # requests' usage from being counted again.
        with get_usage_metadata_callback() as usage:
            try:
                result = agent.invoke(
                    {"messages": [{"role": "user", "content": question}]},
                    config=config,
                )

                print("\nAgent:")
                show_text(result["messages"][-1])

            except GraphRecursionError:
                print(
                    "Execution-step limit reached. "
                    "Use /new before retrying."
                )

            except KeyboardInterrupt:
                print("\nRequest interrupted. Use /new before retrying.")

            except Exception as exc:
                print(f"Request failed: {exc}")

            finally:
                # Reports usage from completed model calls even if a
                # later step fails. Failed calls may lack usage metadata.
                show_usage(usage)


if __name__ == "__main__":
    main()