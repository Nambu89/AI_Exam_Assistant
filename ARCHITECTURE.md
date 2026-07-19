# Architecture

This document explains *why* the system is built the way it is. For the HTTP
surface see [docs/API.md](docs/API.md); for setup see the [README](README.md).

## Design principles

1. **Grounded or silent.** Every answer and every exam question is derived from
   the study corpus and carries its sources. Agents are instructed to abstain
   when the context doesn't support an answer; question generation validates the
   correct answer against the source before it is served.
2. **Runs offline, scales to Azure.** A single `MODEL_PROVIDER` switch flips the
   app between a credential-free local mode (for a first run, for CI, and for
   contributors without a subscription) and full Azure AI Foundry. The agent
   graph, the API and the tests are identical across modes.
3. **Isolate the fast-moving bits.** Anything version-sensitive in the Microsoft
   Agent Framework lives behind one factory module, so SDK churn touches one file.
4. **Evaluate agents like code.** Quality is a CI gate, not a vibe.

## Component map

| Layer | Module | Responsibility |
|---|---|---|
| API | `app/main.py`, `app/api/routes.py` | FastAPI app, CORS, REST + SSE endpoints |
| Orchestration | `app/agents/orchestrator.py` | Guardrails → route → dispatch; the always-on path |
| | `app/agents/af_orchestration.py` | Framework-native Handoff / Concurrent / Magentic (cloud showcase) |
| Agents | `app/agents/{router,tutor,exam,question_generator,validator,analytics}_agent.py` | The specialists |
| Agent runtime | `app/clients/agent_factory.py` | The **only** place that imports Agent Framework |
| Knowledge | `app/knowledge/{factory,foundry_iq,graphrag_service,local_corpus,concept_graph}.py` | Retrieval + concept map |
| Models | `app/models/schemas.py` | Pydantic contracts (mirror docs/API.md) |
| Security | `app/security/guardrails.py` | Lexical + Azure Content Safety layers |
| Evaluation | `evals/` | Offline metric gate + optional Azure agentic evaluators |

## The multi-agent flow

```
user → guardrails → Coordinator (gpt-5-nano) ─┬─ tutor      → retrieve → answer (grounded, cited)
                                              ├─ exam       → QuestionGenerator → Validator → grade
                                              └─ analytics  → weak-topic detection → study plan
```

The **coordinator** is a cheap classifier (a fast model in the cloud, keyword
routing offline). The **exam** path is a real multi-step pipeline: the
`QuestionGeneratorAgent` drafts MCQs grounded in retrieved context; the
`ValidatorAgent` drops anything malformed or unsupported; a deterministic builder
tops up if validation removes questions — so the endpoint never returns garbage.

The cloud path additionally showcases the framework's **native orchestration
patterns** (`af_orchestration.py`): *Handoff* (triage → subject tutor),
*Concurrent* (parallel graders over one essay), and *Magentic* (a manager that
plans an open-ended study task).

## Knowledge strategy: Foundry IQ + GraphRAG (they complement each other)

- **Foundry IQ** (Azure AI Foundry's managed knowledge layer, agentic retrieval
  over Azure AI Search) is the **primary RAG engine** for per-question grounding:
  permission-aware, low operational cost, no index pipeline to maintain. Microsoft
  reports up to **+54% recall** vs single-shot RAG.
- **GraphRAG** (OSS) is the **differentiator**: it extracts an entity/relationship
  graph, clusters it into communities, and summarises them — enabling the
  **concept map** and true **global** ("main themes / exam coverage") answers that
  vector RAG can't produce.

They are not redundant: agentic retrieval doesn't build a concept graph, and
GraphRAG isn't a managed permission-aware service. We use both.

### Query-mode strategy (GraphRAG)

| Use case | Mode | Rationale |
|---|---|---|
| Conversational tutoring | **DRIFT** | local detail + community context, supports follow-ups |
| Factual lookup ("what is X?") | **Local** | entity-centric, cheap |
| "Main topics / what's on the exam?" | **Global** | map-reduce over community reports |
| Grounded question generation | **Global → Local** | Global for balanced topic coverage, Local to anchor each question to a source |

> **Known issue:** GraphRAG issue #1642 — DRIFT search is unreliable on the Azure
> AI Search vector store. We keep **LanceDB** as the GraphRAG vector store (see
> `backend/graphrag/settings.yaml`).

### Cost control

GraphRAG entity extraction is ~75% of indexing cost, so `settings.yaml` points
extraction at the cheap `gpt-5-nano` deployment and reserves `gpt-5.4-mini` for
community reports and answers.

## Offline mode: how it stays honest

Offline mode never fakes an LLM. Instead:
- **Retrieval** → a lexical TF-IDF-ish search over the Markdown corpus (`local_corpus.py`).
- **Tutor** → an extractive answer stitched from the top retrieved sentences, with sources.
- **Exams** → the deterministic grounded builder mines `"<Concept> is/are/provides …"`
  sentences and turns them into MCQs whose correct answer is a real sentence and
  whose distractors are definitions of other concepts.
- **Concept map** → a co-occurrence graph over capitalised concept phrases.

Everything is grounded and cited; nothing is invented. That's what makes the
offline demo trustworthy and the eval gate meaningful without a model.

## Evaluation

`evals/run_eval.py` runs the gold set through the orchestrator and computes
deterministic, offline metrics (lexical groundedness, keyword recall, source
coverage) with a pass/fail gate. With `--mode azure` it additionally runs the
`azure-ai-evaluation` evaluators (Groundedness, Relevance, Intent Resolution)
using `gpt-5-mini` as judge — Microsoft's documented recommendation. CI wires the
gate into `.github/workflows/agent-eval.yml`.

## Security & governance

Defense in depth: a lexical prompt-injection filter (always on) plus optional
**Azure AI Content Safety**. In the cloud, secrets are managed identities via
Key Vault; observability is OpenTelemetry → Application Insights. The app never
processes confidential data and the demo corpus is public study material.

**Network isolation** (`deployPrivateNetworking=true`, the default): all backing
services — Azure AI Foundry/AIServices, Azure AI Search, Key Vault and the
container registry — are reached over **Private Endpoints (Private Link)** inside
a dedicated **VNet**, with `publicNetworkAccess: Disabled` and default-deny
network ACLs, and the Container Apps environment is VNet-injected. The web app's
ingress is the only public surface. Set the flag to `false` to fall back to the
public + managed-identity setup (e.g. when you lack networking quota). See
[`infra/README.md`](infra/README.md).

## <a name="version-notes"></a>Version notes (verified 2026-07-19)

- **Microsoft Agent Framework** GA `1.11` (unifies AutoGen + Semantic Kernel).
  Two constructor surfaces (`chat_client.as_agent(...)` and `ChatAgent(...)`)
  coexisted in the post-GA docs; `agent_factory.py` tries the newer one and falls
  back. The Foundry IQ context-provider import path was also unsettled — confirm
  against your installed version. Both are isolated so churn is a one-file change.
- **GraphRAG** `3.1.1` (MIT). The former `graphrag-accelerator` is archived; we use
  the library directly.
- **Foundry IQ** partially GA (Search REST API `2026-04-01`); some features
  (document-level permissions, answer synthesis) remained preview.
- Models: **GPT-5 family**, EU Data Zone. Never the GPT-4 family.
