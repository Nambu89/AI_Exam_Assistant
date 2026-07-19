/**
 * In-memory implementation of the documented API, used when VITE_USE_MOCKS is
 * on. Adds realistic latency and simulates SSE token streaming so every page
 * behaves as it would against the live FastAPI backend.
 */
import type {
  AgentRoute,
  AnalyticsRequest,
  AnalyticsResponse,
  ChatMode,
  ChatRequest,
  ChatResponse,
  ChatStreamEvent,
  ConceptMapResponse,
  ExamGenerateRequest,
  ExamGenerateResponse,
  ExamGradeRequest,
  ExamGradeResponse,
  ExamQuestion,
  HealthResponse,
  PerQuestionResult,
  TopicsResponse,
} from "@/types/api";
import {
  CHAT_ANSWERS,
  CONCEPT_MAP,
  FALLBACK_ANSWER,
  FALLBACK_SOURCES,
  QUESTION_BANK,
  TOPICS_RESPONSE,
} from "./fixtures";

const delay = (ms: number): Promise<void> => new Promise((resolve) => setTimeout(resolve, ms));

const uid = (): string =>
  globalThis.crypto?.randomUUID?.() ??
  `id-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 8)}`;

function pickRoute(message: string): AgentRoute {
  const m = message.toLowerCase();
  if (/\b(quiz|exam|test me|practice question|mock exam)\b/.test(m)) return "exam";
  if (/\b(progress|how am i doing|weak|score|analytics|improve)\b/.test(m)) return "analytics";
  return "tutor";
}

function pickAnswer(message: string): { answer: string; sources: string[] } {
  const m = message.toLowerCase();
  for (const entry of CHAT_ANSWERS) {
    if (entry.keywords.some((k) => m.includes(k))) {
      return { answer: entry.answer, sources: entry.sources };
    }
  }
  return { answer: FALLBACK_ANSWER, sources: FALLBACK_SOURCES };
}

export async function mockHealth(): Promise<HealthResponse> {
  await delay(120);
  return {
    status: "ok",
    provider: "mock",
    knowledge_backend: "graphrag",
    version: "0.1.0",
  };
}

export async function mockTopics(): Promise<TopicsResponse> {
  await delay(180);
  return structuredClone(TOPICS_RESPONSE);
}

export async function mockChat(req: ChatRequest): Promise<ChatResponse> {
  await delay(500);
  const route = pickRoute(req.message);
  const { answer, sources } = pickAnswer(req.message);
  const mode: ChatMode = req.mode ?? "drift";
  return {
    response: answer,
    agent_used: route,
    route,
    mode,
    sources,
    session_id: req.session_id ?? uid(),
  };
}

/** Tokenise into small chunks to emulate streaming. */
function tokenise(text: string): string[] {
  return text.match(/\S+\s*|\n/g) ?? [text];
}

/** Simulated SSE stream: yields the same event sequence as the real endpoint. */
export async function* mockChatStream(
  req: ChatRequest,
  signal?: AbortSignal,
): AsyncGenerator<ChatStreamEvent> {
  const route = pickRoute(req.message);
  const { answer, sources } = pickAnswer(req.message);
  const sessionId = req.session_id ?? uid();

  await delay(250);
  if (signal?.aborted) return;
  yield { type: "route", agent: route };

  for (const chunk of tokenise(answer)) {
    if (signal?.aborted) return;
    await delay(18 + Math.random() * 34);
    yield { type: "token", text: chunk };
  }

  yield { type: "sources", sources };
  yield { type: "done", session_id: sessionId };
}

export async function mockExamGenerate(req: ExamGenerateRequest): Promise<ExamGenerateResponse> {
  await delay(700);
  const wanted = req.topics && req.topics.length > 0 ? new Set(req.topics) : null;
  const pool = QUESTION_BANK.filter((q) => (wanted ? wanted.has(q.topic) : true));
  const source = pool.length > 0 ? pool : QUESTION_BANK;

  const questions: ExamQuestion[] = [];
  for (let i = 0; i < req.num_questions; i++) {
    const base = source[i % source.length];
    if (!base) break;
    // Fresh, stable per-exam id; content stays grounded to the source item.
    questions.push({ ...base, id: `q${i + 1}` });
  }

  return {
    exam_id: uid(),
    subject: req.subject,
    questions,
  };
}

export async function mockExamGrade(req: ExamGradeRequest): Promise<ExamGradeResponse> {
  await delay(600);
  const answerMap = new Map(req.answers.map((a) => [a.question_id, a.choice]));

  const per_question: PerQuestionResult[] = req.questions.map((q) => {
    const yourChoice = answerMap.get(q.id) ?? null;
    return {
      question_id: q.id,
      your_choice: yourChoice,
      correct: q.correct,
      is_correct: yourChoice === q.correct,
      explanation: q.explanation,
      topic: q.topic,
    };
  });

  const total = per_question.length;
  const correct_count = per_question.filter((p) => p.is_correct).length;
  const score = total > 0 ? Number((correct_count / total).toFixed(4)) : 0;

  // Weak topics: those with at least one wrong answer, worst first.
  const byTopic = new Map<string, { wrong: number; total: number }>();
  for (const p of per_question) {
    const rec = byTopic.get(p.topic) ?? { wrong: 0, total: 0 };
    rec.total += 1;
    if (!p.is_correct) rec.wrong += 1;
    byTopic.set(p.topic, rec);
  }
  const weak_topics = [...byTopic.entries()]
    .filter(([, r]) => r.wrong > 0)
    .sort((a, b) => b[1].wrong / b[1].total - a[1].wrong / a[1].total)
    .map(([topic]) => topic);

  const recommendations =
    weak_topics.length > 0
      ? weak_topics.map((t) => `Review "${t}" — revisit the study notes and retry a focused quiz.`)
      : ["Strong result across all topics. Try a harder difficulty or a broader topic mix."];

  return { score, correct_count, total, per_question, weak_topics, recommendations };
}

export async function mockConceptMap(subject: string): Promise<ConceptMapResponse> {
  await delay(400);
  return { ...structuredClone(CONCEPT_MAP), subject };
}

export async function mockAnalytics(req: AnalyticsRequest): Promise<AnalyticsResponse> {
  await delay(350);
  const byTopic = new Map<string, number[]>();
  for (const h of req.history) {
    const arr = byTopic.get(h.topic) ?? [];
    arr.push(h.score);
    byTopic.set(h.topic, arr);
  }

  const averaged = [...byTopic.entries()].map(([topic, scores]) => ({
    topic,
    avg: scores.reduce((s, v) => s + v, 0) / scores.length,
  }));

  const weak_topics = averaged
    .filter((t) => t.avg < 0.6)
    .sort((a, b) => a.avg - b.avg)
    .map((t) => t.topic);

  const recommendations =
    weak_topics.length > 0
      ? weak_topics.map(
          (t) =>
            `Prioritise "${t}" (avg ${(byTopicAvg(averaged, t) * 100).toFixed(0)}%). Do a short focused quiz, then re-test.`,
        )
      : req.history.length > 0
        ? [
            "You're above the 60% bar on every topic tracked. Push difficulty to consolidate mastery.",
          ]
        : ["No exam history yet — run a practice exam to unlock personalised recommendations."];

  const focus_plan =
    weak_topics.length > 0
      ? [
          `Day 1-2: Re-read notes for ${weak_topics.slice(0, 2).join(" & ")}.`,
          "Day 3: Take a 10-question focused quiz on the weakest topic.",
          "Day 4: Review explanations and the concept map for missed items.",
          "Day 5: Full mock exam across all topics to confirm progress.",
        ]
      : ["Maintain a weekly full mock exam.", "Explore the concept map to connect topics."];

  return { weak_topics, recommendations, focus_plan };
}

function byTopicAvg(averaged: { topic: string; avg: number }[], topic: string): number {
  return averaged.find((a) => a.topic === topic)?.avg ?? 0;
}
