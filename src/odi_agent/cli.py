"""Terminal chat with token tracking and failed-request diagnostics."""

import json
from pathlib import Path
from uuid import uuid4

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
    """Show reported token usage across this request's model calls."""
    metadata = usage.usage_metadata

    print("\n--- Model token usage for this request ---")

    if not metadata:
        print("Token usage was not reported by the model integration.")
        return

    # Cache and reasoning counts are breakdowns of the totals.
    # Do not add them to input/output totals again.
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


def save_failure_trace(agent, config, request_id, error):
    """Inspect saved state without making another model or tool call."""
    try:
        state = agent.get_state(config)
        messages = state.values.get("messages", [])

        # Capture only the current request, not the entire conversation.
        last_user_index = next(
            (
                index
                for index in range(len(messages) - 1, -1, -1)
                if messages[index].type == "human"
            ),
            len(messages),
        )

        trace = []

        for message in messages[last_user_index:]:
            if message.type == "human":
                trace.append({
                    "type": "user",
                    "content": message.content,
                })

            elif message.type == "ai":
                trace.append({
                    "type": "assistant",
                    "content": message.content,
                    "tool_calls": message.tool_calls,
                    "usage": getattr(message, "usage_metadata", None),
                })

            elif message.type == "tool":
                trace.append({
                    "type": "tool_result",
                    "name": message.name,
                    "tool_call_id": message.tool_call_id,
                    "content": message.content,
                })

        # Resolve logs relative to the project, not the terminal folder.
        project_root = Path(__file__).resolve().parents[2]
        log_dir = project_root / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)

        # Unique filename preserves earlier failures for comparison.
        trace_path = log_dir / f"failed_request_{request_id}.json"

        trace_path.write_text(
            json.dumps(
                {
                    "request_id": request_id,
                    "thread_id": config["configurable"]["thread_id"],
                    "error": str(error),
                    "messages": trace,
                },
                indent=2,
                default=str,
            ),
            encoding="utf-8",
        )

        print(f"Diagnostic trace saved: {trace_path}")

    except Exception as trace_error:
        # A logging failure must not hide the original request error.
        print(f"Could not save diagnostic trace: {trace_error}")


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

        request_id = uuid4().hex

        # Reset the usage collector for each new user request.
        with get_usage_metadata_callback() as usage:
            try:
                result = agent.invoke(
                    {"messages": [{"role": "user", "content": question}]},
                    config=config,
                )

                print("\nAgent:")
                show_text(result["messages"][-1])

            except GraphRecursionError as exc:
                print("Execution-step limit reached.")
                save_failure_trace(agent, config, request_id, exc)
                print("Use /new before retrying.")

            except KeyboardInterrupt:
                print("\nRequest interrupted. Use /new before retrying.")

            except Exception as exc:
                print(f"Request failed: {exc}")
                save_failure_trace(agent, config, request_id, exc)
                print("Use /new before retrying.")

            finally:
                # Completed calls may have consumed tokens even if
                # the overall request failed.
                show_usage(usage)


if __name__ == "__main__":
    main()