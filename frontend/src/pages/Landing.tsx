import { BrainCircuit, GitGraph, MessagesSquare, ShieldCheck, Sparkles } from "lucide-react";
import { Link } from "react-router-dom";
import { Badge } from "@/components/ui/Badge";
import { buttonClass } from "@/components/ui/Button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";

const STACK = [
  "Microsoft Agent Framework",
  "Azure AI Foundry",
  "Foundry IQ",
  "GraphRAG",
  "GPT-5 family",
  "Agent evaluations",
];

const FEATURES = [
  {
    icon: MessagesSquare,
    title: "Grounded multi-agent tutor",
    body: "A coordinator routes you to specialist agents. Every answer is grounded in the study corpus and cites its sources.",
  },
  {
    icon: BrainCircuit,
    title: "Adaptive, traceable exams",
    body: "Questions are generated and validated against the material — no invented facts — then graded with per-topic feedback.",
  },
  {
    icon: GitGraph,
    title: "GraphRAG concept map",
    body: "See how syllabus concepts connect, and ask true syllabus-wide questions a plain RAG chatbot can't answer.",
  },
  {
    icon: ShieldCheck,
    title: "Evaluated in CI",
    body: "Agents are tested like code: a groundedness + citation gate runs on every change, with optional Azure agentic evaluators.",
  },
];

export default function Landing() {
  return (
    <div className="space-y-16 py-8">
      <section className="relative overflow-hidden rounded-2xl border border-border bg-card px-6 py-16 text-center">
        <div className="bg-grid pointer-events-none absolute inset-0 opacity-60" aria-hidden />
        <div className="relative mx-auto max-w-3xl space-y-6">
          <Badge tone="primary" className="mx-auto">
            <Sparkles className="size-3.5" /> Open-source · built on Microsoft's 2026 AI stack
          </Badge>
          <h1 className="text-4xl font-bold tracking-tight sm:text-5xl">
            Turn any syllabus into a grounded, multi-agent study companion.
          </h1>
          <p className="text-lg text-muted-foreground">
            Ask questions, sit adaptive practice exams, and explore a concept map of your material —
            all grounded in the source and evaluated for quality.
          </p>
          <div className="flex flex-wrap justify-center gap-3">
            <Link to="/tutor" className={buttonClass({ size: "lg" })}>
              Try the tutor
            </Link>
            <Link to="/map" className={buttonClass({ size: "lg", variant: "outline" })}>
              Explore the concept map
            </Link>
          </div>
          <div className="flex flex-wrap justify-center gap-2 pt-2">
            {STACK.map((s) => (
              <Badge key={s} tone="neutral">
                {s}
              </Badge>
            ))}
          </div>
        </div>
      </section>

      <section className="grid gap-4 sm:grid-cols-2">
        {FEATURES.map((f) => (
          <Card key={f.title}>
            <CardHeader>
              <div className="flex size-10 items-center justify-center rounded-lg bg-primary-soft text-primary">
                <f.icon className="size-5" aria-hidden />
              </div>
              <CardTitle>{f.title}</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground">{f.body}</p>
            </CardContent>
          </Card>
        ))}
      </section>

      <section className="rounded-2xl border border-border bg-muted/40 p-8 text-center">
        <h2 className="text-2xl font-semibold">Runs offline, scales to Azure</h2>
        <p className="mx-auto mt-2 max-w-2xl text-muted-foreground">
          Clone and run with no keys — a deterministic, grounded demo over an Azure Fundamentals
          (AZ-900) corpus. Flip one switch to run the full Microsoft stack: GPT-5 on Azure AI
          Foundry, Foundry IQ agentic retrieval, and real GraphRAG indexing.
        </p>
        <div className="mt-6 flex justify-center">
          <Link to="/exam" className={buttonClass({ variant: "secondary" })}>
            Take a practice exam
          </Link>
        </div>
      </section>
    </div>
  );
}
