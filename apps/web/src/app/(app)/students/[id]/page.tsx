"use client";

/** Teacher/admin: one student's progress, topic accuracy, risk factors and recent quizzes. */
import { useParams, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { AlertTriangle, ArrowLeft, Mail } from "lucide-react";

import RiskBadge from "@/components/teacher/RiskBadge";
import { Avatar, Card, CardHeader, EmptyState, ProgressBar, Skeleton } from "@/components/ui";
import { api } from "@/lib/api";
import { useRequireRole } from "@/lib/useRequireRole";
import { formatDate } from "@/lib/utils";
import type { StudentDetail } from "@/types";

export default function StudentDetailPage() {
  const ok = useRequireRole(["teacher", "admin"]);
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const [s, setS] = useState<StudentDetail | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!ok) return;
    api.get<StudentDetail>(`/teacher/students/${id}`).then(setS).catch((e) => setError(e instanceof Error ? e.message : "Not found"));
  }, [id, ok]);

  if (!ok) return null;
  if (error) return <EmptyState icon={<AlertTriangle className="h-5 w-5" />} title="Student not found" description={error} />;
  if (!s) return <div className="space-y-4"><Skeleton className="h-32" /><Skeleton className="h-64" /></div>;

  return (
    <div className="space-y-6">
      <button onClick={() => router.push("/students")} className="inline-flex min-h-[44px] items-center gap-2 text-sm font-semibold text-muted hover:text-ink">
        <ArrowLeft className="h-4 w-4" /> All students
      </button>

      <Card className="p-5 sm:p-6">
        <div className="flex items-center gap-4">
          <Avatar name={s.name} size="lg" />
          <div className="min-w-0 flex-1">
            <h1 className="truncate font-display text-2xl font-extrabold text-ink">{s.name}</h1>
            <a href={`mailto:${s.email}`} className="inline-flex items-center gap-1.5 truncate text-sm text-brand-600"><Mail className="h-3.5 w-3.5" />{s.email}</a>
          </div>
          <RiskBadge risk={s.risk} />
        </div>
        <div className="mt-5 grid grid-cols-3 gap-3 text-center">
          <div className="rounded-2xl bg-mist/70 p-3"><p className="font-display text-xl font-extrabold">{s.avg_score ?? "—"}{s.avg_score !== null && "%"}</p><p className="text-[11px] text-muted">Avg score</p></div>
          <div className="rounded-2xl bg-mist/70 p-3"><p className="font-display text-xl font-extrabold">{s.completion}%</p><p className="text-[11px] text-muted">Completion</p></div>
          <div className="rounded-2xl bg-mist/70 p-3"><p className="font-display text-xl font-extrabold">{s.attempts}</p><p className="text-[11px] text-muted">Quizzes taken</p></div>
        </div>
        <p className="mt-3 text-xs text-muted">Last active: {formatDate(s.last_active)}</p>
      </Card>

      {s.risk.factors.length > 0 && (
        <Card className="border-amber-200 bg-amber-50/60 p-5">
          <p className="flex items-center gap-2 font-semibold text-amber-800"><AlertTriangle className="h-4 w-4" /> Why this student is flagged</p>
          <ul className="mt-2 list-disc space-y-1 pl-5 text-sm text-amber-900">{s.risk.factors.map((f) => <li key={f}>{f}</li>)}</ul>
        </Card>
      )}

      <div className="grid gap-6 lg:grid-cols-2">
        <Card className="p-5 sm:p-6">
          <CardHeader title="Course progress" />
          <div className="mt-4 space-y-4">
            {s.course_progress.map((c) => (
              <div key={c.id}>
                <div className="flex justify-between gap-2 text-sm"><span className="truncate font-medium text-ink">{c.title}</span><span className="shrink-0 text-muted">{c.lessons_completed}/{c.lessons_total} · {c.completion}%</span></div>
                <ProgressBar value={c.completion} size="sm" className="mt-1.5" />
              </div>
            ))}
          </div>
        </Card>
        <Card className="p-5 sm:p-6">
          <CardHeader title="Topic accuracy" subtitle="Below 60% = weak topic." />
          <div className="mt-4 space-y-4">
            {s.topic_scores.length === 0 && <p className="text-sm text-muted">No quiz data yet.</p>}
            {s.topic_scores.map((t) => (
              <div key={t.topic_id}>
                <div className="flex justify-between text-sm"><span className="truncate font-medium text-ink">{t.topic}</span><span className={t.score < 60 ? "font-semibold text-rose-600" : "text-muted"}>{t.score}%</span></div>
                <ProgressBar value={t.score} size="sm" className="mt-1.5" barClassName={t.score < 60 ? "bg-rose-500" : undefined} />
              </div>
            ))}
          </div>
        </Card>
      </div>

      <Card className="p-5 sm:p-6">
        <CardHeader title="Recent quizzes" />
        <div className="mt-3 divide-y divide-line/70">
          {s.recent_attempts.length === 0 && <p className="py-2 text-sm text-muted">No attempts yet.</p>}
          {s.recent_attempts.map((a) => (
            <div key={a.id} className="flex items-center justify-between gap-3 py-3">
              <div className="min-w-0"><p className="truncate text-sm font-medium text-ink">{a.lesson}</p><p className="text-xs text-muted">{formatDate(a.created_at)}</p></div>
              <span className={`text-sm font-bold ${a.score < 60 ? "text-rose-600" : "text-emerald-600"}`}>{Math.round(a.score)}%</span>
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
}
