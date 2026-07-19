/** Client-held exam history (localStorage). Feeds the Dashboard/Analytics view. */
import type { HistoryEntry } from "@/types/api";
import { logger } from "./logger";

const KEY = "aiea-exam-history";

export interface TopicBreakdown {
  topic: string;
  correct: number;
  total: number;
}

export interface StoredExamResult {
  id: string;
  subject: string;
  date: string; // ISO
  score: number; // 0..1
  correct: number;
  total: number;
  topics: TopicBreakdown[];
}

export function getHistory(): StoredExamResult[] {
  try {
    const raw = localStorage.getItem(KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw) as StoredExamResult[];
    return Array.isArray(parsed) ? parsed : [];
  } catch (err) {
    logger.warn("Failed to read exam history", err);
    return [];
  }
}

export function addResult(result: StoredExamResult): StoredExamResult[] {
  const next = [result, ...getHistory()].slice(0, 50);
  try {
    localStorage.setItem(KEY, JSON.stringify(next));
  } catch (err) {
    logger.warn("Failed to persist exam history", err);
  }
  return next;
}

export function clearHistory(): void {
  try {
    localStorage.removeItem(KEY);
  } catch (err) {
    logger.warn("Failed to clear exam history", err);
  }
}

/** Flatten stored results into the per-topic history the analytics API expects. */
export function toHistoryEntries(results: StoredExamResult[]): HistoryEntry[] {
  const entries: HistoryEntry[] = [];
  for (const r of results) {
    for (const t of r.topics) {
      entries.push({
        subject: r.subject,
        topic: t.topic,
        score: t.total > 0 ? t.correct / t.total : 0,
      });
    }
  }
  return entries;
}
