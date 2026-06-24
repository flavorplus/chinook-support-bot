from collections.abc import Mapping
from typing import Any


def get_message_content(message: Any) -> str:
    content = getattr(message, "content", None)
    if content is None and isinstance(message, Mapping):
        content = message.get("content")
    if content is None:
        text = getattr(message, "text", None)
        if callable(text):
            text = text()
        content = text
    return content if isinstance(content, str) else str(content or "")


def run_chat_loop(agent: Any, config: dict[str, Any] | None = None) -> None:
    messages: list[Any] = []

    while True:
        user_input = input("You: ").strip()
        if not user_input:
            continue
        if user_input.lower() in {"exit", "quit", "q"}:
            print("Goodbye.")
            break

        messages.append({"role": "user", "content": user_input})
        result = agent.invoke({"messages": messages}, config=config)
        messages = result["messages"]
        print(f"Bot: {get_message_content(messages[-1])}\n")
