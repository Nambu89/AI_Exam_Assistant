import type { ApiError } from "@/types/api";
import { apiUrl } from "./config";

/** Error thrown by the HTTP client; carries the FastAPI `detail`/`reason`. */
export class HttpError extends Error {
  readonly status: number;
  readonly reason?: string;

  constructor(status: number, detail: string, reason?: string) {
    super(detail);
    this.name = "HttpError";
    this.status = status;
    this.reason = reason;
  }
}

async function parseError(res: Response): Promise<HttpError> {
  let detail = `Request failed (${res.status})`;
  let reason: string | undefined;
  try {
    const body = (await res.json()) as ApiError;
    if (body.detail) detail = body.detail;
    reason = body.reason;
  } catch {
    /* non-JSON error body; keep the generic message */
  }
  return new HttpError(res.status, detail, reason);
}

/** Typed JSON GET. */
export async function getJson<T>(path: string, signal?: AbortSignal): Promise<T> {
  const res = await fetch(apiUrl(path), {
    method: "GET",
    headers: { Accept: "application/json" },
    signal,
  });
  if (!res.ok) throw await parseError(res);
  return (await res.json()) as T;
}

/** Typed JSON POST. */
export async function postJson<T>(path: string, body: unknown, signal?: AbortSignal): Promise<T> {
  const res = await fetch(apiUrl(path), {
    method: "POST",
    headers: { "Content-Type": "application/json", Accept: "application/json" },
    body: JSON.stringify(body),
    signal,
  });
  if (!res.ok) throw await parseError(res);
  return (await res.json()) as T;
}
