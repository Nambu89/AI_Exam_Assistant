# API Contract — AI Exam Assistant

Single source of truth for the HTTP API. Backend (FastAPI) and frontend (React)
both conform to this. Base path: `/api`. All request/response bodies are JSON
unless noted. CORS allows the configured frontend origins.

## Health & metadata

### `GET /api/health`
```json
{ "status": "ok", "provider": "local", "knowledge_backend": "graphrag", "version": "0.1.0" }
```

### `GET /api/topics`
Returns study subjects/topics discovered in the corpus.
```json
{ "subjects": [{ "id": "az-900", "title": "Azure Fundamentals", "topics": ["Cloud Concepts", "Azure Architecture", "..."] }] }
```

## Chat (multi-agent tutor)

### `POST /api/chat`  (non-streaming)
Request:
```json
{ "message": "What is an Availability Zone?", "session_id": "optional-uuid", "mode": "drift" }
```
`mode` ∈ `local | global | drift` (optional; the orchestrator picks a sensible default).
Response:
```json
{
  "response": "…grounded answer…",
  "agent_used": "tutor",
  "route": "tutor",
  "mode": "drift",
  "sources": ["az-900/02-azure-architecture.md#Availability Zones"],
  "session_id": "uuid"
}
```

### `POST /api/chat/stream`  (Server-Sent Events, `text/event-stream`)
Same request body. Emits events, each `data:` line is a JSON object:
- `{ "type": "route", "agent": "tutor" }`
- `{ "type": "token", "text": "partial…" }`  (repeated)
- `{ "type": "sources", "sources": ["…"] }`
- `{ "type": "done", "session_id": "uuid" }`
- `{ "type": "error", "message": "…" }`

## Exams

### `POST /api/exam/generate`
Request:
```json
{ "subject": "az-900", "topics": ["Storage"], "num_questions": 5, "difficulty": "medium" }
```
`topics` optional (empty ⇒ all). `difficulty` ∈ `easy | medium | hard`.
Response:
```json
{
  "exam_id": "uuid",
  "subject": "az-900",
  "questions": [
    {
      "id": "q1",
      "stem": "Which redundancy option …?",
      "options": { "A": "LRS", "B": "ZRS", "C": "GRS", "D": "GZRS" },
      "correct": "D",
      "explanation": "…grounded rationale…",
      "topic": "Storage",
      "sources": ["az-900/04-storage.md#Redundancy"]
    }
  ]
}
```
> The frontend hides `correct`/`explanation` until the exam is graded.

### `POST /api/exam/grade`
Request:
```json
{ "exam_id": "uuid", "questions": [ … as returned above … ], "answers": [ { "question_id": "q1", "choice": "B" } ] }
```
Response:
```json
{
  "score": 0.6,
  "correct_count": 3,
  "total": 5,
  "per_question": [ { "question_id": "q1", "your_choice": "B", "correct": "D", "is_correct": false, "explanation": "…", "topic": "Storage" } ],
  "weak_topics": ["Storage"],
  "recommendations": ["Review Storage redundancy tiers (LRS/ZRS/GRS/GZRS)."]
}
```

## Concept map (GraphRAG differentiator)

### `GET /api/concept-map?subject=az-900&level=1`
Nodes come from GraphRAG entities/communities (or an offline co-occurrence graph).
```json
{
  "subject": "az-900",
  "backend": "graphrag",
  "nodes": [ { "id": "Availability Zone", "label": "Availability Zone", "community": 2, "size": 7 } ],
  "edges": [ { "source": "Availability Zone", "target": "Azure Region", "weight": 3 } ],
  "communities": [ { "id": 2, "title": "Azure global infrastructure", "summary": "…" } ]
}
```

## Analytics

### `POST /api/analytics/recommendations`
Request: `{ "history": [ { "subject": "az-900", "topic": "Storage", "score": 0.4 } ] }`
Response: `{ "weak_topics": ["Storage"], "recommendations": ["…"], "focus_plan": ["…"] }`

## Errors
Non-2xx responses use `{ "detail": "message" }` (FastAPI default). Guardrail
blocks return `400` with `{ "detail": "blocked", "reason": "…" }`.
