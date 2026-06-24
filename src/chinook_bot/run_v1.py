import argparse
import os

from dotenv import load_dotenv

from .chat_loop import run_chat_loop
from .v1_agent import (
    V1_LANGSMITH_PROJECT,
    create_v1_agent,
    get_v1_run_config,
)
from .v1_context import SupportContext
from .v1_repository import get_customer_profile


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the Chinook support bot v1.")
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

    customer_name = f"{profile['FirstName']} {profile['LastName']}"
    context = SupportContext(
        customer_id=args.customer_id,
        customer_name=customer_name,
    )
    agent = create_v1_agent(
        context,
        enable_pii_middleware=args.pii_middleware,
    )

    print(
        f"Starting Chinook support bot v1 for customer "
        f"{context.customer_id} {context.customer_name}"
    )
    print("Type a question and press Enter. Type exit or quit to stop.")
    print(
        "PII middleware: "
        f"{'enabled' if args.pii_middleware else 'disabled'}"
    )

    try:
        run_chat_loop(
            agent,
            config=get_v1_run_config(
                context,
                pii_middleware_enabled=args.pii_middleware,
            ),
        )
    except KeyboardInterrupt:
        print("\nInterrupted. Exiting.")


if __name__ == "__main__":
    main()
