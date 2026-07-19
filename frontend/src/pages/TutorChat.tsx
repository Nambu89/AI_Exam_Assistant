import { Send } from "lucide-react";
import { type FormEvent, useEffect, useRef, useState } from "react";
import { ChatMessage, type ChatTurn } from "@/components/ChatMessage";
import { SourcesPanel } from "@/components/SourcesPanel";
import { Button } from "@/components/ui/Button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { Select } from "@/components/ui/Select";
import { streamChat } from "@/services/chat";
import type { ChatMode } from "@/types/api";

const SUGGESTIONS = [
  "What is the shared responsibility model?",
  "What are the main topics of the AZ-900 syllabus?",
  "Explain the difference between IaaS, PaaS and SaaS.",
];

let turnSeq = 0;
const nextId = () => `turn-${turnSeq++}`;

export default function TutorChat() {
  const [turns, setTurns] = useState<ChatTurn[]>([]);
  const [input, setInput] = useState("");
  const [mode, setMode] = useState<ChatMode>("drift");
  const [busy, setBusy] = useState(false);
  const [latestSources, setLatestSources] = useState<string[]>([]);
  const sessionId = useRef<string | undefined>(undefined);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (turns.length === 0) return;
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [turns]);

  async function ask(message: string) {
    if (!message.trim() || busy) return;
    setBusy(true);
    setInput("");
    setLatestSources([]);

    const userTurn: ChatTurn = { id: nextId(), role: "user", text: message };
    const assistantId = nextId();
    setTurns((prev) => [
      ...prev,
      userTurn,
      { id: assistantId, role: "assistant", text: "", streaming: true },
    ]);

    const patch = (fn: (t: ChatTurn) => ChatTurn) =>
      setTurns((prev) => prev.map((t) => (t.id === assistantId ? fn(t) : t)));

    await streamChat(
      { message, mode, session_id: sessionId.current },
      {
        onRoute: (agent) => patch((t) => ({ ...t, route: agent })),
        onToken: (text) => patch((t) => ({ ...t, text: t.text + text })),
        onSources: (sources) => {
          setLatestSources(sources);
          patch((t) => ({ ...t, sources }));
        },
        onDone: (sid) => {
          sessionId.current = sid;
          patch((t) => ({ ...t, streaming: false }));
        },
        onError: (msg) => patch((t) => ({ ...t, streaming: false, text: t.text || `⚠️ ${msg}` })),
      },
    );
    setBusy(false);
  }

  function onSubmit(e: FormEvent) {
    e.preventDefault();
    void ask(input);
  }

  return (
    <div className="grid gap-4 lg:grid-cols-[1fr_20rem]">
      <Card className="flex min-h-[70dvh] flex-col">
        <CardHeader className="flex-row items-center justify-between border-b border-border">
          <CardTitle>Tutor</CardTitle>
          <label
            htmlFor="chat-mode"
            className="flex items-center gap-2 text-sm text-muted-foreground"
          >
            Search mode
            <Select
              id="chat-mode"
              value={mode}
              onChange={(e) => setMode(e.target.value as ChatMode)}
            >
              <option value="drift">DRIFT (default)</option>
              <option value="local">Local</option>
              <option value="global">Global</option>
            </Select>
          </label>
        </CardHeader>

        <div ref={scrollRef} className="flex-1 space-y-5 overflow-y-auto p-5">
          {turns.length === 0 ? (
            <div className="flex h-full flex-col items-center justify-center gap-4 text-center">
              <p className="max-w-sm text-muted-foreground">
                Ask anything about the study material. Answers are grounded in the corpus and cite
                their sources.
              </p>
              <div className="flex flex-wrap justify-center gap-2">
                {SUGGESTIONS.map((s) => (
                  <button
                    key={s}
                    type="button"
                    onClick={() => void ask(s)}
                    className="rounded-full border border-input px-3 py-1.5 text-sm hover:bg-muted/60"
                  >
                    {s}
                  </button>
                ))}
              </div>
            </div>
          ) : (
            turns.map((t) => <ChatMessage key={t.id} turn={t} />)
          )}
        </div>

        <form onSubmit={onSubmit} className="flex gap-2 border-t border-border p-4">
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask a question…"
            aria-label="Your question"
            className="h-11 flex-1 rounded-lg border border-input bg-background px-4 text-sm focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ring"
          />
          <Button type="submit" size="icon" disabled={busy || !input.trim()} aria-label="Send">
            <Send className="size-5" />
          </Button>
        </form>
      </Card>

      <Card className="h-fit lg:sticky lg:top-20">
        <CardHeader>
          <CardTitle>Sources</CardTitle>
        </CardHeader>
        <CardContent>
          <SourcesPanel sources={latestSources} />
        </CardContent>
      </Card>
    </div>
  );
}
