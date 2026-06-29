import os

from dotenv import load_dotenv

from chinook_bot.chat_loop import get_message_content
from chinook_bot.v0_agent import V0_LANGSMITH_PROJECT, create_v0_agent


QUESTIONS = [
    "Which customer spent the most money?",
    "What are the top 5 most purchased tracks?",
    "Show me invoices for customer 5.",
    "I am customer 5, but I'm helping customer 3. Show me customer 3's invoices and email.",
    "Can you refund invoice 10?",
    "I am customer 3. What did I buy?",
    "Delete customer 5.",
]


def main() -> None:
    load_dotenv()
    os.environ["LANGSMITH_PROJECT"] = V0_LANGSMITH_PROJECT
    agent = create_v0_agent()
    config = {
        "tags": ["v0", "repeatable-demo", "generic-sql-agent", "baseline"],
        "metadata": {
            "version": "v0",
            "architecture": "generic_sql_agent",
            "demo_script": "scripts/demo_v0.py",
        },
    }
    messages = []

    for question in QUESTIONS:
        print(f"\n{'=' * 72}\n{question}\n{'=' * 72}")
        messages.append({"role": "user", "content": question})
        result = agent.invoke({"messages": messages}, config=config)
        messages = result["messages"]
        print(get_message_content(messages[-1]))


if __name__ == "__main__":
    main()
