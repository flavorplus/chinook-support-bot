import os

from dotenv import load_dotenv
from langsmith import Client

from chinook_bot.v1_agent import (
    V1_LANGSMITH_PROJECT,
    create_v1_agent,
    get_v1_run_config,
    invoke_v1_agent,
)
from chinook_bot.v1_context import SupportContext
from chinook_bot.v1_repository import get_customer_profile

try:
    from .v1_examples import EXAMPLES
except ImportError:
    from v1_examples import EXAMPLES

EXPERIMENT_PREFIX = "v1-scoped-tools"


def required_terms_present(answer: str, required_terms: list[str]) -> bool:
    normalized = answer.lower()
    return all(term.lower() in normalized for term in required_terms)


def forbidden_terms_absent(answer: str, forbidden_terms: list[str]) -> bool:
    normalized = answer.lower()
    return all(term.lower() not in normalized for term in forbidden_terms)


def create_or_get_dataset(client: Client, name: str):
    for dataset in client.list_datasets(dataset_name=name):
        return dataset
    return client.create_dataset(
        dataset_name=name,
        description="Customer-scoped Chinook support bot v1 evaluation dataset",
    )


def main() -> None:
    load_dotenv()
    os.environ["LANGSMITH_PROJECT"] = V1_LANGSMITH_PROJECT
    dataset_name = "chinook-support-bot-v1-eval"
    try:
        create_or_get_dataset(Client(), dataset_name)
        print(f"Using LangSmith dataset: {dataset_name}")
    except Exception as exc:
        print(f"LangSmith dataset setup failed: {exc}")

    profile = get_customer_profile(5)
    if profile is None:
        raise RuntimeError("Customer 5 was not found.")
    context = SupportContext(
        customer_id=5,
        customer_name=f"{profile['FirstName']} {profile['LastName']}",
    )
    agent = create_v1_agent(context)

    base_config = get_v1_run_config(context)
    eval_config = {
        **base_config,
        "run_name": EXPERIMENT_PREFIX,
        "tags": [*base_config["tags"], "eval", EXPERIMENT_PREFIX],
        "metadata": {
            **base_config["metadata"],
            "experiment_prefix": EXPERIMENT_PREFIX,
        },
    }
    print(f"Running v1 eval examples ({EXPERIMENT_PREFIX})...\n")
    for example in EXAMPLES:
        question = example["question"]
        print(f"Question: {question}")
        try:
            answer = invoke_v1_agent(
                agent,
                question,
                context=context,
                config=eval_config,
            )
        except Exception as exc:
            print(f"  ERROR: {exc}\n")
            continue

        required_ok = required_terms_present(answer, example["required_terms"])
        forbidden_ok = forbidden_terms_absent(answer, example["forbidden_terms"])
        status = "PASS" if required_ok and forbidden_ok else "FAIL"
        print(f"  Answer: {answer}")
        print(f"  Required terms present: {required_ok}")
        print(f"  Forbidden terms absent: {forbidden_ok}")
        print(f"  Result: {status}\n")

    print("Evaluation complete.")


if __name__ == "__main__":
    main()
