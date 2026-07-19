import { Loader2 } from "lucide-react";
import { useState } from "react";
import { QuestionCard } from "@/components/QuestionCard";
import { Button } from "@/components/ui/Button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { Select } from "@/components/ui/Select";
import { useTopics } from "@/hooks/queries";
import { addResult } from "@/lib/history";
import { api } from "@/services/api";
import type { Choice, Difficulty, ExamGenerateResponse, ExamGradeResponse } from "@/types/api";

type Phase = "config" | "taking" | "graded";
const SUBJECT = "az-900";

export default function ExamRunner() {
  const { data: topicsData } = useTopics();
  const subject = topicsData?.subjects.find((s) => s.id === SUBJECT);
  const allTopics = subject?.topics ?? [];

  const [phase, setPhase] = useState<Phase>("config");
  const [selectedTopics, setSelectedTopics] = useState<string[]>([]);
  const [numQuestions, setNumQuestions] = useState(5);
  const [difficulty, setDifficulty] = useState<Difficulty>("medium");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [exam, setExam] = useState<ExamGenerateResponse | null>(null);
  const [answers, setAnswers] = useState<Record<string, Choice>>({});
  const [result, setResult] = useState<ExamGradeResponse | null>(null);

  function toggleTopic(topic: string) {
    setSelectedTopics((prev) =>
      prev.includes(topic) ? prev.filter((t) => t !== topic) : [...prev, topic],
    );
  }

  async function generate() {
    setLoading(true);
    setError(null);
    try {
      const e = await api.examGenerate({
        subject: SUBJECT,
        topics: selectedTopics,
        num_questions: numQuestions,
        difficulty,
      });
      setExam(e);
      setAnswers({});
      setResult(null);
      setPhase("taking");
    } catch {
      setError("Could not generate the exam. Is the backend running (or mocks enabled)?");
    } finally {
      setLoading(false);
    }
  }

  async function submit() {
    if (!exam) return;
    setLoading(true);
    setError(null);
    try {
      const graded = await api.examGrade({
        exam_id: exam.exam_id,
        questions: exam.questions,
        answers: exam.questions.map((q) => ({ question_id: q.id, choice: answers[q.id] ?? "A" })),
      });
      setResult(graded);
      setPhase("graded");
      persist(exam, graded);
    } catch {
      setError("Could not grade the exam.");
    } finally {
      setLoading(false);
    }
  }

  function reset() {
    setPhase("config");
    setExam(null);
    setResult(null);
    setAnswers({});
  }

  const answeredCount = Object.keys(answers).length;

  if (phase === "config") {
    return (
      <div className="mx-auto max-w-2xl">
        <Card>
          <CardHeader>
            <CardTitle>New practice exam</CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
            <div>
              <p className="mb-2 text-sm font-medium">Topics (none = all)</p>
              <div className="flex flex-wrap gap-2">
                {allTopics.map((t) => (
                  <button
                    key={t}
                    type="button"
                    aria-pressed={selectedTopics.includes(t)}
                    onClick={() => toggleTopic(t)}
                    className={
                      selectedTopics.includes(t)
                        ? "rounded-full border border-primary bg-primary-soft px-3 py-1.5 text-sm text-primary"
                        : "rounded-full border border-input px-3 py-1.5 text-sm hover:bg-muted/60"
                    }
                  >
                    {t}
                  </button>
                ))}
              </div>
            </div>

            <div className="flex flex-wrap gap-6">
              <label htmlFor="num-questions" className="flex flex-col gap-1 text-sm font-medium">
                Questions
                <Select
                  id="num-questions"
                  value={numQuestions}
                  onChange={(e) => setNumQuestions(Number(e.target.value))}
                >
                  {[3, 5, 10].map((n) => (
                    <option key={n} value={n}>
                      {n}
                    </option>
                  ))}
                </Select>
              </label>
              <label htmlFor="difficulty" className="flex flex-col gap-1 text-sm font-medium">
                Difficulty
                <Select
                  id="difficulty"
                  value={difficulty}
                  onChange={(e) => setDifficulty(e.target.value as Difficulty)}
                >
                  <option value="easy">Easy</option>
                  <option value="medium">Medium</option>
                  <option value="hard">Hard</option>
                </Select>
              </label>
            </div>

            {error && <p className="text-sm text-danger">{error}</p>}
            <Button onClick={() => void generate()} disabled={loading} size="lg">
              {loading && <Loader2 className="size-4 animate-spin" />}
              Generate exam
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (phase === "taking" && exam) {
    return (
      <div className="mx-auto max-w-2xl space-y-4">
        <div className="flex items-center justify-between">
          <h1 className="text-xl font-semibold">Practice exam</h1>
          <span className="text-sm text-muted-foreground">
            {answeredCount}/{exam.questions.length} answered
          </span>
        </div>
        {exam.questions.map((q, i) => (
          <Card key={q.id}>
            <CardContent className="pt-5">
              <QuestionCard
                question={q}
                index={i}
                selected={answers[q.id] ?? null}
                onSelect={(c) => setAnswers((prev) => ({ ...prev, [q.id]: c }))}
              />
            </CardContent>
          </Card>
        ))}
        {error && <p className="text-sm text-danger">{error}</p>}
        <div className="flex gap-3">
          <Button onClick={() => void submit()} disabled={loading} size="lg">
            {loading && <Loader2 className="size-4 animate-spin" />}
            Submit &amp; grade
          </Button>
          <Button variant="ghost" onClick={reset}>
            Cancel
          </Button>
        </div>
      </div>
    );
  }

  if (phase === "graded" && exam && result) {
    return (
      <div className="mx-auto max-w-2xl space-y-4">
        <Card>
          <CardContent className="flex flex-wrap items-center justify-between gap-4 pt-6">
            <div>
              <p className="text-4xl font-bold text-primary">{Math.round(result.score * 100)}%</p>
              <p className="text-sm text-muted-foreground">
                {result.correct_count} of {result.total} correct
              </p>
            </div>
            <div className="text-sm">
              {result.weak_topics.length > 0 ? (
                <>
                  <p className="font-medium">Focus next on:</p>
                  <p className="text-muted-foreground">{result.weak_topics.join(", ")}</p>
                </>
              ) : (
                <p className="text-success">Great — no weak topics detected!</p>
              )}
            </div>
            <Button onClick={reset}>New exam</Button>
          </CardContent>
        </Card>

        {result.recommendations.length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle>Recommendations</CardTitle>
            </CardHeader>
            <CardContent>
              <ul className="list-inside list-disc space-y-1 text-sm text-muted-foreground">
                {result.recommendations.map((r) => (
                  <li key={r}>{r}</li>
                ))}
              </ul>
            </CardContent>
          </Card>
        )}

        {exam.questions.map((q, i) => (
          <Card key={q.id}>
            <CardContent className="pt-5">
              <QuestionCard
                question={q}
                index={i}
                selected={answers[q.id] ?? null}
                onSelect={() => {}}
                graded
              />
            </CardContent>
          </Card>
        ))}
      </div>
    );
  }

  return null;
}

function persist(exam: ExamGenerateResponse, result: ExamGradeResponse) {
  const byTopic = new Map<string, { correct: number; total: number }>();
  for (const p of result.per_question) {
    const rec = byTopic.get(p.topic) ?? { correct: 0, total: 0 };
    rec.total += 1;
    if (p.is_correct) rec.correct += 1;
    byTopic.set(p.topic, rec);
  }
  addResult({
    id: exam.exam_id,
    subject: exam.subject,
    date: new Date().toISOString(),
    score: result.score,
    correct: result.correct_count,
    total: result.total,
    topics: [...byTopic.entries()].map(([topic, r]) => ({
      topic,
      correct: r.correct,
      total: r.total,
    })),
  });
}
