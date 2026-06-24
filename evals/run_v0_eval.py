import os
from pathlib import Path
from dotenv import load_dotenv
from langsmith import Client
from .v0_examples import EXAMPLES
from chinook_bot.v0_agent import (
    V0_LANGSMITH_PROJECT,
    V0_RUN_CONFIG,
    create_v0_agent,
    invoke_v0_agent,
)

EXPERIMENT_PREFIX = "v0-baseline"


def create_or_get_dataset(client: Client, name: str):
    for dataset in client.list_datasets(dataset_name=name):
        return dataset
    return client.create_dataset(
        dataset_name=name,
        description="Chinook support bot v0 evaluation dataset",
    )


def main() -> None:
    load_dotenv()
    os.environ["LANGSMITH_PROJECT"] = V0_LANGSMITH_PROJECT
    client = Client()
    dataset_name = "chinook-support-bot-v0-eval"
    try:
        dataset = create_or_get_dataset(client, dataset_name)
        print(f"Using LangSmith dataset: {dataset_name}")
    except Exception as exc:
        print(f"LangSmith dataset creation failed: {exc}")
        dataset = None

    db_path = Path(__file__).resolve().parents[1] / "data" / "Chinook.db"
    agent = create_v0_agent(str(db_path))

    eval_config = {
        **V0_RUN_CONFIG,
        "run_name": EXPERIMENT_PREFIX,
        "tags": [*V0_RUN_CONFIG["tags"], "eval", EXPERIMENT_PREFIX],
        "metadata": {
            **V0_RUN_CONFIG["metadata"],
            "experiment_prefix": EXPERIMENT_PREFIX,
        },
    }
    print(f"Running v0 eval examples ({EXPERIMENT_PREFIX})...\n")
    for example in EXAMPLES:
        question = example["question"]
        required_terms = example["required_terms"]
        print(f"Question: {question}")
        try:
            answer = invoke_v0_agent(agent, question, config=eval_config)
        except Exception as exc:
            print(f"  ERROR: {exc}\n")
            continue
        normalized_answer = answer.lower()
        passed = all(term.lower() in normalized_answer for term in required_terms)
        status = "PASS" if passed else "FAIL"
        print(f"  Answer: {answer}")
        print(f"  Required terms: {required_terms}")
        print(f"  Result: {status}\n")

    print("Evaluation complete.")


if __name__ == "__main__":
    main()
