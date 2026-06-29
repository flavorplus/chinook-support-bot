from typing import Any


def make_config(
    *,
    version: str,
    scenario: str,
    workflow: str,
    architecture: str,
    customer_id: int | None = None,
    pii_middleware_enabled: bool = False,
    extra_tags: list[str] | None = None,
    extra_metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    tags = [
        version,
        "story-demo",
        workflow,
        scenario,
    ]
    if extra_tags:
        tags.extend(extra_tags)

    metadata: dict[str, Any] = {
        "version": version,
        "scenario": scenario,
        "workflow": workflow,
        "architecture": architecture,
        "customer_id": customer_id,
        "pii_middleware_enabled": pii_middleware_enabled,
    }
    if extra_metadata:
        metadata.update(extra_metadata)

    return {
        "run_name": scenario,
        "tags": tags,
        "metadata": metadata,
    }
