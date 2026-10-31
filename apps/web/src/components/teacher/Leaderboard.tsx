"use client";

/** Teacher: ranked class leaderboard (60% quiz average + 40% lesson completion) with certificate eligibility. */
import Link from "next/link";
import { useEffect, useState } from "react";
import { Award, Trophy } from "lucide-react";

import { Avatar, Card, CardHeader, ProgressBar, Skeleton } from "@/components/ui";
import { api } from "@/lib/api";
import type { Course } from "@/types";

interface Leader {
  id: number;
  rank: number;
  name: string;
  points: number;
  avg_score: number | null;
  completion: number;
  lessons_completed: number;
  attempts: number;
  certificate_eligible: boolean;
}

const MEDAL = ["bg-amber-100 text-amber-700", "bg-slate-200 text-slate-600", "bg-orange-100 text-orange-700"];

export default function Leaderboard() {
  const [courses, setCourses] = useState<Course[]>([]);
  const [courseId, setCourseId] = useState("");
  const [rows, setRows] = useState<Leader[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.get<Course[]>("/courses/mine").then(setCourses).catch(() => undefined);
  }, []);

  useEffect(() => {
    setRows(null);
    setError(null);
    api
      .get<{ leaders: Leader[] }>(`/teacher/leaderboard${courseId ? `?course_id=${courseId}` : ""}`)
      .then((d) => setRows(d.leaders))
      .catch((e) => setError(e instanceof Error ? e.message : "Could not load the leaderboard."));
  }, [courseId]);

  return (
    <Card className="p-4 sm:p-6">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <CardHeader title="Leaderboard" subtitle="Ranked by quiz average (60%) and lessons completed (40%)." />
        {courses.length > 1 && (
          <select value={courseId} onChange={(e) => setCourseId(e.target.value)} aria-label="Filter leaderboard by course" className="input-base sm:w-56">
            <option value="">All my courses</option>
            {courses.map((c) => (
              <option key={c.id} value={c.id}>{c.title}</option>
            ))}
          </select>
        )}
      </div>

      {error && <p className="mt-3 rounded-xl bg-rose-50 px-3 py-2 text-sm text-rose-700">{error}</p>}
      {!rows && !error && <div className="mt-4 space-y-2">{[0, 1, 2].map((i) => <Skeleton key={i} className="h-14 w-full" />)}</div>}
      {rows && rows.length === 0 && (
        <p className="mt-4 rounded-2xl bg-mist/70 p-4 text-sm text-muted">
          No students yet. Share your <strong>class code</strong> (open a course, then &ldquo;Manage this course&rdquo;) and students will appear here as they learn.
        </p>
      )}
      {rows && rows.length > 0 && (
        <ol className="mt-4 space-y-2">
          {rows.slice(0, 10).map((r) => (
            <li key={r.id}>
              <Link href={`/students/${r.id}`} className="flex min-h-[60px] items-center gap-3 rounded-2xl border border-line px-3 py-2 hover:bg-mist">
                <span className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-full text-sm font-bold ${MEDAL[r.rank - 1] ?? "bg-mist text-muted"}`}>
                  {r.rank <= 3 ? <Trophy className="h-4 w-4" /> : r.rank}
                </span>
                <Avatar name={r.name} size="sm" />
                <span className="min-w-0 flex-1">
                  <span className="flex items-center gap-2">
                    <span className="truncate text-sm font-semibold text-ink">{r.name}</span>
                    {r.certificate_eligible && (
                      <span className="inline-flex shrink-0 items-center gap-1 rounded-full bg-emerald-50 px-2 py-0.5 text-[11px] font-semibold text-emerald-700">
                        <Award className="h-3 w-3" /> Certified
                      </span>
                    )}
                  </span>
                  <span className="mt-1 block"><ProgressBar value={r.completion} /></span>
                  <span className="mt-0.5 block text-[11px] text-muted">
                    {r.completion}% complete · {r.avg_score === null ? "no quizzes yet" : `${r.avg_score}% quiz avg`}
                  </span>
                </span>
                <span className="shrink-0 text-right">
                  <span className="block font-display text-lg font-extrabold text-ink">{r.points}</span>
                  <span className="block text-[10px] font-semibold uppercase tracking-wide text-muted">pts</span>
                </span>
              </Link>
            </li>
          ))}
        </ol>
      )}
    </Card>
  );
}
