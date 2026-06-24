import os
import sys
from pathlib import Path
from dotenv import load_dotenv

from .chat_loop import run_chat_loop
from .v0_agent import V0_LANGSMITH_PROJECT, V0_RUN_CONFIG, create_v0_agent


def main() -> None:
    load_dotenv()
    os.environ["LANGSMITH_PROJECT"] = V0_LANGSMITH_PROJECT
    db_path = Path(__file__).resolve().parents[2] / "data" / "Chinook.db"
    print("Starting Chinook support bot v0.")
    print("Type a question and press Enter. Type exit or quit to stop.")

    agent = create_v0_agent(str(db_path))

    try:
        run_chat_loop(agent, config=V0_RUN_CONFIG)
    except KeyboardInterrupt:
        print("\nInterrupted. Exiting.")
        sys.exit(0)


if __name__ == "__main__":
    main()
