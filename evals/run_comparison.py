import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from langsmith import Client, tracing_context

from chinook_bot.v0_agent import (
    V0_LANGSMITH_PROJECT,
    V0_RUN_CONFIG,
    create_v0_agent,
    invoke_v0_agent,
)
from chinook_bot.v1_agent import (
    V1_LANGSMITH_PROJECT,
    create_v1_agent,
    get_v1_run_config,
    invoke_v1_agent,
)
from chinook_bot.v1_context import SupportContext
from chinook_bot.v1_repository import get_customer_profile

try:
    from .evaluators import (
        no_bulk_email_leakage,
        no_cross_customer_leakage,
        no_generic_sql_tool_boundary,
        not_empty_and_relevant,
        refund_requires_escalation,
    )
    from .regression_examples import DATASET_NAME, EXAMPLES
except ImportError:
    from evaluators import (
        no_bulk_email_leakage,
        no_cross_customer_leakage,
        no_generic_sql_tool_boundary,
        not_empty_and_relevant,
        refund_requires_escalation,
    )
    from regression_examples import DATASET_NAME, EXAMPLES


V0_EXPERIMENT_PREFIX = "v0-baseline"
V1_EXPERIMENT_PREFIX = "v1-scoped-tools"


def create_or_get_dataset(client: Client, name: str):
    for dataset in client.list_datasets(dataset_name=name):
        return dataset
    return client.create_dataset(
        dataset_name=name,
        description=(
            "Shared regression suite for comparing the v0 generic SQL bot "
            "with the v1 scoped-tool bot."
        ),
    )


def sync_examples(client: Client, dataset_name: str) -> None:
    existing_by_question = {
        example.inputs.get("question"): example
        for example in client.list_examples(dataset_name=dataset_name)
    }
    for example in EXAMPLES:
        question = example["inputs"]["question"]
        existing = existing_by_question.get(question)
        if existing is None:
            client.create_example(dataset_name=dataset_name, **example)
        else:
            client.update_example(
                existing.id,
                inputs=example["inputs"],
                outputs=example["outputs"],
                metadata=example["metadata"],
            )


def make_v0_target() -> Any:
    os.environ["LANGSMITH_PROJECT"] = V0_LANGSMITH_PROJECT
    db_path = Path(__file__).resolve().parents[1] / "data" / "Chinook.db"
    agent = create_v0_agent(str(db_path))
    config = {
        **V0_RUN_CONFIG,
        "tags": [*V0_RUN_CONFIG["tags"], "eval", V0_EXPERIMENT_PREFIX],
        "metadata": {
            **V0_RUN_CONFIG["metadata"],
            "experiment_prefix": V0_EXPERIMENT_PREFIX,
            "dataset": DATASET_NAME,
        },
    }

    def target(inputs: dict) -> dict:
        os.environ["LANGSMITH_PROJECT"] = V0_LANGSMITH_PROJECT
        return {"answer": invoke_v0_agent(agent, inputs["question"], config=config)}

    return target


def make_v1_target() -> Any:
    os.environ["LANGSMITH_PROJECT"] = V1_LANGSMITH_PROJECT
    profile = get_customer_profile(5)
    if profile is None:
        raise RuntimeError("Customer 5 was not found.")
    context = SupportContext(
        customer_id=5,
        customer_name=f"{profile['FirstName']} {profile['LastName']}",
    )
    agent = create_v1_agent(context)
    base_config = get_v1_run_config(context)
    config = {
        **base_config,
        "tags": [*base_config["tags"], "eval", V1_EXPERIMENT_PREFIX],
        "metadata": {
            **base_config["metadata"],
            "experiment_prefix": V1_EXPERIMENT_PREFIX,
            "dataset": DATASET_NAME,
        },
    }

    def target(inputs: dict) -> dict:
        os.environ["LANGSMITH_PROJECT"] = V1_LANGSMITH_PROJECT
        return {
            "answer": invoke_v1_agent(
                agent,
                inputs["question"],
                context=context,
                config=config,
            )
        }

    return target


def run_experiment(
    client: Client,
    target: Any,
    project_name: str,
    experiment_prefix: str,
    metadata: dict[str, Any],
):
    os.environ["LANGSMITH_PROJECT"] = project_name
    with tracing_context(project_name=project_name, parent=False):
        return client.evaluate(
            target,
            data=DATASET_NAME,
            evaluators=[
                not_empty_and_relevant,
                no_cross_customer_leakage,
                no_bulk_email_leakage,
                refund_requires_escalation,
                no_generic_sql_tool_boundary,
            ],
            experiment_prefix=experiment_prefix,
            metadata=metadata,
            description=(
                "Shared Chinook support bot regression eval for architecture comparison."
            ),
            max_concurrency=0,
            blocking=True,
        )


def main() -> None:
    load_dotenv()
    client = Client()
    create_or_get_dataset(client, DATASET_NAME)
    sync_examples(client, DATASET_NAME)
    print(f"Using shared LangSmith dataset: {DATASET_NAME}")

    print(f"Running experiment: {V0_EXPERIMENT_PREFIX}")
    run_experiment(
        client=client,
        target=make_v0_target(),
        project_name=V0_LANGSMITH_PROJECT,
        experiment_prefix=V0_EXPERIMENT_PREFIX,
        metadata={
            "version": "v0",
            "architecture": "generic_sql_agent",
            "data_access": "generic_sql_tools",
            "safety_model": "prompt_and_basic_sql_blocking",
            "dataset": DATASET_NAME,
        },
    )

    print(f"Running experiment: {V1_EXPERIMENT_PREFIX}")
    run_experiment(
        client=client,
        target=make_v1_target(),
        project_name=V1_LANGSMITH_PROJECT,
        experiment_prefix=V1_EXPERIMENT_PREFIX,
        metadata={
            "version": "v1",
            "architecture": "scoped_business_tools",
            "data_access": "trusted_application_session_context",
            "safety_model": "tool_level_customer_scoping",
            "dataset": DATASET_NAME,
            "customer_id": 5,
        },
    )

    print("Comparison eval complete.")
    print(f"Dataset: {DATASET_NAME}")
    print(f"Experiments: {V0_EXPERIMENT_PREFIX}, {V1_EXPERIMENT_PREFIX}")


if __name__ == "__main__":
    main()
