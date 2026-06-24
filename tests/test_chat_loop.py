from dataclasses import dataclass

from chinook_bot.chat_loop import get_message_content, run_chat_loop


@dataclass
class Message:
    content: str


class FakeAgent:
    def __init__(self) -> None:
        self.invocations: list[list] = []
        self.configs: list[dict | None] = []

    def invoke(self, payload: dict, config: dict | None = None) -> dict:
        messages = list(payload["messages"])
        self.invocations.append(messages)
        self.configs.append(config)
        user_message = messages[-1]["content"]
        return {"messages": [*messages, Message(f"Answer to {user_message}")]}


def test_chat_loop_preserves_returned_message_history(monkeypatch, capsys) -> None:
    inputs = iter(["first question", "", "follow up", "quit"])
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))
    agent = FakeAgent()

    config = {"tags": ["test"], "metadata": {"version": "test"}}
    run_chat_loop(agent, config=config)

    assert len(agent.invocations) == 2
    assert agent.configs == [config, config]
    assert agent.invocations[1] == [
        {"role": "user", "content": "first question"},
        Message("Answer to first question"),
        {"role": "user", "content": "follow up"},
    ]
    output = capsys.readouterr().out
    assert "Bot: Answer to first question" in output
    assert "Bot: Answer to follow up" in output
    assert "Goodbye." in output


def test_get_message_content_supports_objects_and_mappings() -> None:
    assert get_message_content(Message("object content")) == "object content"
    assert get_message_content({"content": "mapping content"}) == "mapping content"
