/**
 * Chat streaming. Presents one callback interface regardless of whether the
 * tokens come from the mock generator or a live SSE endpoint
 * (`POST /api/chat/stream`, `text/event-stream`).
 */
import { mockChatStream } from "@/mocks/mockApi";
import type { ChatRequest, ChatStreamEvent } from "@/types/api";
import { apiUrl, USE_MOCKS } from "./config";
import { HttpError } from "./http";

export interface StreamCallbacks {
  onRoute?: (agent: string) => void;
  onToken?: (text: string) => void;
  onSources?: (sources: string[]) => void;
  onDone?: (sessionId: string) => void;
  onError?: (message: string) => void;
}

function dispatch(event: ChatStreamEvent, cb: StreamCallbacks): void {
  switch (event.type) {
    case "route":
      cb.onRoute?.(event.agent);
      break;
    case "token":
      cb.onToken?.(event.text);
      break;
    case "sources":
      cb.onSources?.(event.sources);
      break;
    case "done":
      cb.onDone?.(event.session_id);
      break;
    case "error":
      cb.onError?.(event.message);
      break;
  }
}

async function streamFromMock(
  req: ChatRequest,
  cb: StreamCallbacks,
  signal?: AbortSignal,
): Promise<void> {
  for await (const event of mockChatStream(req, signal)) {
    dispatch(event, cb);
  }
}

async function streamFromServer(
  req: ChatRequest,
  cb: StreamCallbacks,
  signal?: AbortSignal,
): Promise<void> {
  const res = await fetch(apiUrl("/api/chat/stream"), {
    method: "POST",
    headers: { "Content-Type": "application/json", Accept: "text/event-stream" },
    body: JSON.stringify(req),
    signal,
  });

  if (!res.ok || !res.body) {
    throw new HttpError(res.status, `Stream failed (${res.status})`);
  }

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });

    // SSE frames are separated by a blank line.
    let sep: number = buffer.indexOf("\n\n");
    while (sep !== -1) {
      const frame = buffer.slice(0, sep);
      buffer = buffer.slice(sep + 2);
      for (const line of frame.split("\n")) {
        const trimmed = line.trimStart();
        if (!trimmed.startsWith("data:")) continue;
        const payload = trimmed.slice(5).trim();
        if (!payload) continue;
        try {
          dispatch(JSON.parse(payload) as ChatStreamEvent, cb);
        } catch {
          /* ignore keep-alive / malformed frames */
        }
      }
      sep = buffer.indexOf("\n\n");
    }
  }
}

/** Start a streamed chat turn. Resolves when the stream ends. */
export async function streamChat(
  req: ChatRequest,
  cb: StreamCallbacks,
  signal?: AbortSignal,
): Promise<void> {
  try {
    if (USE_MOCKS) {
      await streamFromMock(req, cb, signal);
    } else {
      await streamFromServer(req, cb, signal);
    }
  } catch (err) {
    if (signal?.aborted) return;
    cb.onError?.(err instanceof Error ? err.message : "Unknown streaming error");
  }
}
