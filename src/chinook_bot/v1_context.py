from dataclasses import dataclass


@dataclass
class SupportContext:
    customer_id: int
    customer_name: str | None = None
    support_tier: str = "standard"
