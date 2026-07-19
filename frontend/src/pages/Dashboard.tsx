import { Trash2 } from "lucide-react";
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Badge } from "@/components/ui/Badge";
import { Button, buttonClass } from "@/components/ui/Button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { clearHistory, getHistory, type StoredExamResult, toHistoryEntries } from "@/lib/history";
import { api } from "@/services/api";
import type { AnalyticsResponse } from "@/types/api";

export default function Dashboard() {
  const [history, setHistory] = useState<StoredExamResult[]>([]);
  const [analytics, setAnalytics] = useState<AnalyticsResponse | null>(null);

  useEffect(() => {
    const h = getHistory();
    setHistory(h);
    if (h.length > 0) {
      api
        .analytics({ history: toHistoryEntries(h) })
        .then(setAnalytics)
        .catch(() => setAnalytics(null));
    }
  }, []);

  function onClear() {
    clearHistory();
    setHistory([]);
    setAnalytics(null);
  }

  const avg =
    history.length > 0
      ? Math.round((history.reduce((s, r) => s + r.score, 0) / history.length) * 100)
      : 0;

  if (history.length === 0) {
    return (
      <div className="mx-auto max-w-lg py-16 text-center">
        <h1 className="text-2xl font-semibold">Your dashboard</h1>
        <p className="mt-2 text-muted-foreground">
          Take a practice exam to unlock progress tracking and personalised recommendations.
        </p>
        <Link to="/exam" className={`${buttonClass()} mt-6`}>
          Take your first exam
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Your dashboard</h1>
        <Button variant="ghost" size="sm" onClick={onClear}>
          <Trash2 className="size-4" /> Clear history
        </Button>
      </div>

      <div className="grid gap-4 sm:grid-cols-3">
        <Card>
          <CardContent className="pt-6">
            <p className="text-3xl font-bold text-primary">{avg}%</p>
            <p className="text-sm text-muted-foreground">Average score</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <p className="text-3xl font-bold">{history.length}</p>
            <p className="text-sm text-muted-foreground">Exams taken</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <p className="text-3xl font-bold">{analytics?.weak_topics.length ?? 0}</p>
            <p className="text-sm text-muted-foreground">Weak topics</p>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Recent exams</CardTitle>
          </CardHeader>
          <CardContent>
            <ul className="divide-y divide-border">
              {history.map((r) => (
                <li key={r.id} className="flex items-center justify-between py-2 text-sm">
                  <span className="text-muted-foreground">
                    {new Date(r.date).toLocaleDateString()} · {r.subject}
                  </span>
                  <Badge tone={r.score >= 0.6 ? "success" : "warning"}>
                    {Math.round(r.score * 100)}%
                  </Badge>
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Study plan</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4 text-sm">
            {analytics ? (
              <>
                {analytics.recommendations.length > 0 && (
                  <ul className="list-inside list-disc space-y-1 text-muted-foreground">
                    {analytics.recommendations.map((r) => (
                      <li key={r}>{r}</li>
                    ))}
                  </ul>
                )}
                {analytics.focus_plan.length > 0 && (
                  <ol className="list-inside list-decimal space-y-1">
                    {analytics.focus_plan.map((f) => (
                      <li key={f}>{f}</li>
                    ))}
                  </ol>
                )}
              </>
            ) : (
              <p className="text-muted-foreground">Loading recommendations…</p>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
