/**
 * Types mirroring docs/API.md exactly. This is the shared contract with the
 * FastAPI backend — do not add fields or endpoints beyond the documented API.
 */

export type ChatMode = "local" | "global" | "drift";
export type AgentRoute = "tutor" | "exam" | "analytics";
export type Difficulty = "easy" | "medium" | "hard";
export type Choice = "A" | "B" | "C" | "D";

/** GET /api/health */
export interface HealthResponse {
  status: string;
  provider: string;
  knowledge_backend: string;
  version: string;
}

/** GET /api/topics */
export interface Subject {
  id: string;
  title: string;
  topics: string[];
}
export interface TopicsResponse {
  subjects: Subject[];
}

/** POST /api/chat (non-streaming) */
export interface ChatRequest {
  message: string;
  session_id?: string;
  mode?: ChatMode;
}
export interface ChatResponse {
  response: string;
  agent_used: string;
  route: AgentRoute;
  mode: ChatMode;
  sources: string[];
  session_id: string;
}

/** POST /api/chat/stream — one JSON object per SSE `data:` line. */
export type ChatStreamEvent =
  | { type: "route"; agent: AgentRoute }
  | { type: "token"; text: string }
  | { type: "sources"; sources: string[] }
  | { type: "done"; session_id: string }
  | { type: "error"; message: string };

/** POST /api/exam/generate */
export interface ExamGenerateRequest {
  subject: string;
  topics?: string[];
  num_questions: number;
  difficulty: Difficulty;
}
export interface ExamQuestion {
  id: string;
  stem: string;
  options: Record<Choice, string>;
  correct: Choice;
  explanation: string;
  topic: string;
  sources: string[];
}
export interface ExamGenerateResponse {
  exam_id: string;
  subject: string;
  questions: ExamQuestion[];
}

/** POST /api/exam/grade */
export interface ExamAnswer {
  question_id: string;
  choice: Choice;
}
export interface ExamGradeRequest {
  exam_id: string;
  questions: ExamQuestion[];
  answers: ExamAnswer[];
}
export interface PerQuestionResult {
  question_id: string;
  your_choice: Choice | null;
  correct: Choice;
  is_correct: boolean;
  explanation: string;
  topic: string;
}
export interface ExamGradeResponse {
  score: number;
  correct_count: number;
  total: number;
  per_question: PerQuestionResult[];
  weak_topics: string[];
  recommendations: string[];
}

/** GET /api/concept-map */
export interface ConceptNode {
  id: string;
  label: string;
  community: number;
  size: number;
}
export interface ConceptEdge {
  source: string;
  target: string;
  weight: number;
}
export interface ConceptCommunity {
  id: number;
  title: string;
  summary: string;
}
export interface ConceptMapResponse {
  subject: string;
  backend: string;
  nodes: ConceptNode[];
  edges: ConceptEdge[];
  communities: ConceptCommunity[];
}

/** POST /api/analytics/recommendations */
export interface HistoryEntry {
  subject: string;
  topic: string;
  score: number;
}
export interface AnalyticsRequest {
  history: HistoryEntry[];
}
export interface AnalyticsResponse {
  weak_topics: string[];
  recommendations: string[];
  focus_plan: string[];
}

/** FastAPI error envelope. */
export interface ApiError {
  detail: string;
  reason?: string;
}
