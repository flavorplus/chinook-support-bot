# Chinook Support Bot

A local Python demo showing two approaches to customer support over the Chinook SQLite database.

## v0 vs v1

| Version | Identity | Agent tools | Safety model |
| --- | --- | --- | --- |
| v0 | User-provided text | Generic schema and SQL tools | Blocks destructive SQL keywords |
| v1 | Trusted runtime `customer_id` | Narrow customer-support actions | Repository queries are always customer-scoped |

v0 remains available as the intentionally permissive baseline. v1 is the recommended example.

## Setup

1. Create a Python environment:

   python3.11 -m venv .venv
   source .venv/bin/activate

2. Install dependencies:

   python -m pip install --upgrade pip
   python -m pip install -e .

   Python 3.10 or newer is required by LangChain 1.x.

3. Copy environment variables:

   cp .env.example .env
   # Set OPENAI_API_KEY and optionally LANGSMITH_API_KEY for LangSmith tracing.

4. Download the database:

   python scripts/download_chinook.py

## Environment variables

Required:

- `OPENAI_API_KEY` — used by LangChain to call OpenAI.

Optional for tracing:

- `LANGSMITH_TRACING=true`
- `LANGSMITH_ENDPOINT=https://api.smith.langchain.com`
- `LANGSMITH_API_KEY=your-langsmith-key`

The terminal and evaluation runners assign `LANGSMITH_PROJECT` automatically.

## LangSmith tracing

- v0 traces appear in `chinook-support-bot-v0`.
- v1 traces appear in `chinook-support-bot-v1`.
- v0 traces are tagged as the generic SQL agent baseline.
- v1 traces are tagged as scoped business tools using trusted runtime customer context.

The lightweight eval runners use these trace labels:

- v0 experiment prefix: `v0-baseline`
- v1 experiment prefix: `v1-scoped-tools`

This separation makes the generic SQL architecture directly comparable with the customer-scoped v1 architecture.

## How to run v0

Run the local terminal interface:

   python -m chinook_bot.run_v0

Type questions and exit with `quit`, `exit`, or `Ctrl+C`.

## How to run v1

Run v1 for an authenticated customer ID:

   PYTHONPATH=src python -m chinook_bot.run_v1 --customer-id 5

The default customer ID is `5`, so `--customer-id` is optional.

v1 looks up the customer before constructing the agent. The runtime context, not the user message, determines which account the tools can access.

Enable LangChain PII middleware to redact email addresses returned by v1
tools before subsequent model calls:

   PYTHONPATH=src python -m chinook_bot.run_v1 --customer-id 5 --pii-middleware

The middleware is disabled by default so its effect can be demonstrated
explicitly. Repository and tool-level data controls remain active in both modes.

## Repeatable v1 demo

Run the fixed v1 demo flow for customer 5:

   PYTHONPATH=src python scripts/demo_v1.py

Run the same demo with PII middleware enabled:

   PYTHONPATH=src python scripts/demo_v1.py --pii-middleware

The script preserves conversation history while demonstrating authenticated account access, recommendations, follow-up questions, cross-customer privacy, destructive-action refusal, and mock support-case creation. Its traces appear in the `chinook-support-bot-v1` LangSmith project with the `repeatable-demo` tag.

Use another authenticated customer context with:

   PYTHONPATH=src python scripts/demo_v1.py --customer-id 3

## Repeatable v0 demo

Run the fixed generic-SQL baseline demo:

   PYTHONPATH=src python scripts/demo_v0.py

The script preserves conversation history and sends traces to the `chinook-support-bot-v0` LangSmith project with the `repeatable-demo` and `baseline` tags. It still uses the original v0 generic SQL tools and safety model.

## v0 demo questions

- Which customer spent the most money?
- Show me invoices for customer 5.
- What are the top 5 genres by number of tracks?
- Can you refund invoice 10?
- I am customer 3. What did I buy?

## How to run tests

Run pytest from the repository root:

   pytest

The test suite will download the database automatically if it is missing.

## How to run evals

Run the v0 evaluation:

   PYTHONPATH=src python -m evals.run_v0_eval

Run the v1 safety-oriented evaluation:

   PYTHONPATH=src python -m evals.run_v1_eval

The scripts use LangSmith if configured and check for required and forbidden terms.

## v0 limitations

This project is intentionally minimal and not production-safe.

- No authentication or customer identity enforcement.
- No production database permissions or access control.
- No PII filtering.
- No real refund or action workflow.
- Generic SQL access is allowed for this demo.

> This is not safe for production. Use this demo only for local experimentation.

## Why v1 is safer

- The authenticated `customer_id` is supplied through `SupportContext`.
- Agent tools never accept a `customer_id`.
- Every account-specific repository query binds `CustomerId = ?`.
- Invoice lookups return nothing when the invoice belongs to another customer.
- The agent has no arbitrary SQL or schema tools.
- Optional LangChain `PIIMiddleware` redacts email addresses in tool results
  before subsequent model calls.
- Destructive requests are refused.
- Refunds and account changes can only create mock support cases.

Repository and tool-level data minimization remain the primary protection;
middleware is an additional model-boundary safeguard. v1 is still a demo. It
does not implement real authentication, authorization infrastructure, or
durable support cases.

## What v2 could add

A future v2 could include:

- Real authentication and signed session context.
- Role-based support-agent permissions.
- Durable support cases with approval workflows.
- PII redaction and structured audit logs.
- Human confirmation before sensitive actions.
- Policy checks and broader adversarial safety evaluations.
