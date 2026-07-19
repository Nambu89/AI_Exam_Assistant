import { Bot, User } from "lucide-react";
import { Badge } from "@/components/ui/Badge";
import { cn } from "@/lib/cn";

export interface ChatTurn {
  id: string;
  role: "user" | "assistant";
  text: string;
  route?: string;
  sources?: string[];
  streaming?: boolean;
}

const ROUTE_LABEL: Record<string, string> = {
  tutor: "Tutor",
  exam: "Exam",
  analytics: "Analytics",
};

export function ChatMessage({ turn }: { turn: ChatTurn }) {
  const isUser = turn.role === "user";
  return (
    <div className={cn("flex gap-3", isUser && "flex-row-reverse")}>
      <div
        className={cn(
          "flex size-8 shrink-0 items-center justify-center rounded-full",
          isUser ? "bg-muted text-muted-foreground" : "bg-primary-soft text-primary",
        )}
        aria-hidden
      >
        {isUser ? <User className="size-4" /> : <Bot className="size-4" />}
      </div>
      <div className={cn("max-w-[80%] space-y-2", isUser && "items-end text-right")}>
        {!isUser && turn.route && (
          <Badge tone="primary">{ROUTE_LABEL[turn.route] ?? turn.route}</Badge>
        )}
        <div
          className={cn(
            "inline-block whitespace-pre-wrap rounded-xl px-4 py-2.5 text-sm leading-relaxed",
            isUser ? "bg-primary text-primary-foreground" : "bg-card border border-border",
          )}
        >
          {turn.text}
          {turn.streaming && <span className="ml-0.5 animate-pulse">▍</span>}
        </div>
      </div>
    </div>
  );
}
