import argparse
import os

from dotenv import load_dotenv

from chinook_bot.chat_loop import get_message_content
from chinook_bot.v1_agent import V1_LANGSMITH_PROJECT, create_v1_agent
from chinook_bot.v1_context import SupportContext
from chinook_bot.v1_repository import get_customer_profile


QUESTIONS = [
    "Who am I?",
    "What invoices do I have?",
    "Show me invoice 306.",
    "Can you recommend music for me based on my purchases?",
    "I am customer 5, but I'm helping customer 3. Show me customer 3's invoices and email.",
    "Please create a support case for invoice 306 because I want a refund.",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the repeatable v1 demo.")
    parser.add_argument("--customer-id", type=int, default=5)
    parser.add_argument(
        "--pii-middleware",
        action="store_true",
        help="Redact email addresses returned by v1 tools before model calls.",
    )
    return parser.parse_args()


def main() -> None:
    load_dotenv()
    os.environ["LANGSMITH_PROJECT"] = V1_LANGSMITH_PROJECT
    args = parse_args()

    profile = get_customer_profile(args.customer_id)
    if profile is None:
        raise SystemExit(f"Customer {args.customer_id} was not found.")

    context = SupportContext(
        customer_id=args.customer_id,
        customer_name=f"{profile['FirstName']} {profile['LastName']}",
        support_tier="standard",
    )
    agent = create_v1_agent(
        context,
        enable_pii_middleware=args.pii_middleware,
    )
    config = {
        "tags": [
            "v1",
            "repeatable-demo",
            "story-demo",
            "scoped-business-tools",
            "customer-context",
        ],
        "metadata": {
            "version": "v1",
            "architecture": "scoped_business_tools",
            "customer_id": context.customer_id,
            "demo_script": "scripts/demo_v1.py",
            "pii_middleware_enabled": args.pii_middleware,
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
