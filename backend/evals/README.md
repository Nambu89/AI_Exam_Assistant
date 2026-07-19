# Agent Evaluation Harness

This directory holds the **agent-quality gate** for the AI Exam Assistant. It is
the part of the project that most open-source agent projects skip: we evaluate
the *agent's answers* — not just unit tests — on **every push, in CI, with no
secrets required**.

> Why this matters: an agent can pass every unit test and still hallucinate,
> answer off-topic, or drop its citations. Behavioural regressions only show up
> when you score real answers against a known-good dataset. Wiring that into CI
> turns "the agent feels worse today" into a red build.

## The gold dataset

`data/eval/gold_qa.jsonl` (repo root, 20 items). One JSON object per line:

```json
{"question": "...", "ground_truth": "...", "topic": "cloud-concepts", "type": "local"}
```

`type` is `local` (factual lookup) or `global` (holistic / coverage). The harness
maps it onto the retriever's search mode: `type == "global"` → `SearchMode.GLOBAL`,
everything else → `SearchMode.DRIFT` (the conversational default).

## Two evaluation layers

### 1. Offline deterministic gate — always runs in CI

No LLM, no network, no Azure. The harness drives the orchestrator with
`MODEL_PROVIDER=local` (fully offline model provider) and scores each answer with
the **pure functions in `metrics.py`**:

| Metric | What it measures | Formula (all in `[0, 1]`) |
| --- | --- | --- |
| `groundedness_lexical` | Is what the agent said *supported* by trusted text? (precision) | `|content(answer) ∩ content(reference)| / |content(answer)|`, where `reference` = retrieved source text **and** the gold `ground_truth`, and `content(x)` is the set of non-stopword tokens of `x`. |
| `keyword_recall` | Did the agent cover the expected points? (recall) | `|keywords(ground_truth) ∩ content(answer)| / |keywords(ground_truth)|` |
| `has_sources` | Did the agent cite at least one source? | `len(res.sources) > 0` |

**Item passes** iff `groundedness_lexical ≥ --min-groundedness` **AND** `has_sources`.

**Gate passes** iff `pass_rate ≥ --min-pass-rate` **AND** `mean groundedness ≥ --min-groundedness`.
That decision is the process exit code: `0` = gate green, `1` = gate red.

The metrics are intentionally lexical: cheap, reproducible, and impossible to
game with an empty or off-topic answer. They are covered by `test_metrics.py`,
which runs in the normal backend test suite (`pytest backend`) with no network.

`groundedness_lexical` **fails closed**: an answer with no reference to ground
against, or with no content words, scores `0.0`.

### 2. Azure AI Evaluation layer — optional, `--mode azure`

When Azure credentials are present, the harness *additionally* runs Microsoft's
official [`azure-ai-evaluation`](https://learn.microsoft.com/azure/ai-foundry/how-to/develop/evaluate-sdk)
SDK — the LLM-as-a-judge evaluators, including the **agentic** ones:

- **Groundedness** — is the response supported by the retrieved context?
- **Relevance** — does the response address the query?
- **Intent Resolution** — did the agent correctly understand and resolve what the
  user was actually asking for? (agentic evaluator)
- Microsoft's broader agentic suite also includes **Task Adherence** (did the
  agent follow the instructions/plan?) and **Tool Call Accuracy** (did it call
  the right tools with the right arguments?). These plug in the same way as the
  three wired here and are the natural next additions as the agent grows more
  tools.

The judge model is a deployment named by the `JUDGE_MODEL` env var (default
`gpt-5-mini`). **Microsoft's documented recommendation is to use `gpt-5-mini` as
the judge model** for the evaluation SDK — strong reasoning at low cost, so the
judge itself does not dominate the CI bill. (Stack rule LES-G-036: GPT-5 family
only, never GPT-4; and the deployment must be a Data Zone UE deployment.)

This layer is imported **lazily** and **skips cleanly** (logged message, no
failure) when the package is not installed or credentials are absent — so the
offline gate never hard-fails just because Azure is unavailable. Install it with:

```bash
pip install -e '.[eval]'   # azure-ai-evaluation + azure-ai-projects
```

Environment used (first present wins): `AZURE_OPENAI_ENDPOINT` /
`AZURE_AI_ENDPOINT`, `AZURE_OPENAI_API_KEY` / `AZURE_AI_API_KEY` (or
`DefaultAzureCredential` if no key), `JUDGE_MODEL`, `AZURE_OPENAI_API_VERSION`.

## Running it

```bash
# From the repo root (offline gate — this is what CI runs):
python backend/evals/run_eval.py \
  --gold data/eval/gold_qa.jsonl \
  --out eval-report.json \
  --min-groundedness 0.6 \
  --min-pass-rate 0.7

# With the Azure judge layer as well (needs creds in env):
python backend/evals/run_eval.py --gold data/eval/gold_qa.jsonl \
  --out eval-report.json --mode azure --judge-model gpt-5-mini
```

Outputs:

- **`eval-report.json`** — machine-readable: thresholds, per-item metrics + the
  answer/sources/route/agent used, aggregate stats, the Azure layer status, and
  `gate_pass`.
- **Markdown summary on stdout** — a table suitable for `$GITHUB_STEP_SUMMARY`
  (pass with `--summary-out "$GITHUB_STEP_SUMMARY"` to also write it to a file).
- **Exit code** — `0` if all thresholds met, `1` otherwise. This is the gate.

The run is robust: if the orchestrator returns few or no sources, or one item
errors, the harness records it and still produces a full report rather than
crashing.

## How the GitHub Action consumes it

The workflow `.github/workflows/agent-eval.yml` runs the **offline** layer on
every PR (no secrets needed) and uploads the report:

```yaml
name: agent-eval
on: [pull_request, push]

jobs:
  agent-eval:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - name: Install backend
        working-directory: backend
        run: pip install -e '.[dev]'
      - name: Run agent evaluation gate (offline, no secrets)
        env:
          MODEL_PROVIDER: local
        run: |
          python backend/evals/run_eval.py \
            --gold data/eval/gold_qa.jsonl \
            --out eval-report.json \
            --min-groundedness 0.6 --min-pass-rate 0.7 \
            --summary-out "$GITHUB_STEP_SUMMARY"
      - name: Upload eval report
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: eval-report
          path: eval-report.json
```

Because `run_eval.py` exits non-zero when a threshold is missed, a behavioural
regression in the agent turns the PR check red — the same way a failing unit
test does. An optional second job (gated on a `AZURE_OPENAI_ENDPOINT` secret)
can run `--mode azure` on `main` for the richer LLM-judge scores without
blocking day-to-day PRs.

## Files

| File | Purpose |
| --- | --- |
| `run_eval.py` | CLI harness: drives the orchestrator, scores, writes the report, sets the exit code. |
| `metrics.py` | Pure, deterministic scoring functions (offline gate). |
| `test_metrics.py` | Pytest unit tests for `metrics.py` (no network, in the backend suite). |
| `README.md` | This document. |
