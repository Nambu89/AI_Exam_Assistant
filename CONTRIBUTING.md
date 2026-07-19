# Contributing

Thanks for your interest! This project is a reference accelerator, so
contributions that improve clarity, correctness, or the Microsoft-stack showcase
are especially welcome.

## Getting started

```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e "backend[dev]"
cd backend && pytest          # everything runs offline, no credentials
```

Frontend:

```bash
cd frontend && npm install && npm run build
```

## Ground rules

- **Everything must run offline.** `MODEL_PROVIDER=local` is the CI default; new
  features need a credential-free path (deterministic fallback) and unit tests.
- **Stay grounded.** Answers and questions must cite corpus sources. Don't add
  code paths that let the assistant invent facts.
- **Keep Agent Framework imports in `app/clients/agent_factory.py`.** That's the
  single isolation point for SDK changes.
- **Models: GPT-5 family only** (never GPT-4), EU Data Zone in Azure config.
- **Verify before you assert.** Cite Microsoft Learn / official docs (with dates)
  for any new API, SKU, or Azure resource type in your PR description.

## Checks before opening a PR

```bash
cd backend
ruff check . && pytest
python evals/run_eval.py --gold ../data/eval/gold_qa.jsonl --out /tmp/report.json
cd ../frontend && npm run lint && npm run build
```

The agent-evaluation gate (`.github/workflows/agent-eval.yml`) must stay green.

## Adding a new subject/corpus

Drop Markdown files under `data/corpus/<subject>/`, add a gold set if you can,
then (for GraphRAG) `python -m app.ingest --subject <subject> && graphrag index --root backend/graphrag`.

## Reporting issues

Please include repro steps, the mode (`local`/`foundry`), and logs. Security
issues: please disclose privately first.
