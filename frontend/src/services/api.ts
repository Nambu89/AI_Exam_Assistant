/**
 * Typed API client. Every function matches an endpoint in docs/API.md.
 * When USE_MOCKS is on it delegates to the in-app mock layer; otherwise it
 * calls `${VITE_API_URL}/api/...` over HTTP.
 */
import {
  mockAnalytics,
  mockChat,
  mockConceptMap,
  mockExamGenerate,
  mockExamGrade,
  mockHealth,
  mockTopics,
} from "@/mocks/mockApi";
import type {
  AnalyticsRequest,
  AnalyticsResponse,
  ChatRequest,
  ChatResponse,
  ConceptMapResponse,
  ExamGenerateRequest,
  ExamGenerateResponse,
  ExamGradeRequest,
  ExamGradeResponse,
  HealthResponse,
  TopicsResponse,
} from "@/types/api";
import { USE_MOCKS } from "./config";
import { getJson, postJson } from "./http";

export const api = {
  health(signal?: AbortSignal): Promise<HealthResponse> {
    return USE_MOCKS ? mockHealth() : getJson("/api/health", signal);
  },

  topics(signal?: AbortSignal): Promise<TopicsResponse> {
    return USE_MOCKS ? mockTopics() : getJson("/api/topics", signal);
  },

  chat(req: ChatRequest, signal?: AbortSignal): Promise<ChatResponse> {
    // Non-streaming chat; streaming lives in services/chat.ts.
    return USE_MOCKS ? mockChat(req) : postJson("/api/chat", req, signal);
  },

  examGenerate(req: ExamGenerateRequest, signal?: AbortSignal): Promise<ExamGenerateResponse> {
    return USE_MOCKS ? mockExamGenerate(req) : postJson("/api/exam/generate", req, signal);
  },

  examGrade(req: ExamGradeRequest, signal?: AbortSignal): Promise<ExamGradeResponse> {
    return USE_MOCKS ? mockExamGrade(req) : postJson("/api/exam/grade", req, signal);
  },

  conceptMap(subject: string, level = 1, signal?: AbortSignal): Promise<ConceptMapResponse> {
    return USE_MOCKS
      ? mockConceptMap(subject)
      : getJson(`/api/concept-map?subject=${encodeURIComponent(subject)}&level=${level}`, signal);
  },

  analytics(req: AnalyticsRequest, signal?: AbortSignal): Promise<AnalyticsResponse> {
    return USE_MOCKS ? mockAnalytics(req) : postJson("/api/analytics/recommendations", req, signal);
  },
};
