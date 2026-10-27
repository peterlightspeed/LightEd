"use client";

/** Student revision planner (PDF FR-17): pick course + exam date + daily minutes -> day-by-day plan. */
import Link from "next/link";
import { useEffect, useState } from "react";
import { CalendarDays, Clock, RotateCcw } from "lucide-react";

import { Badge, Button, Card, EmptyState, Input, Select } from "@/components/ui";
import { api } from "@/lib/api";
import { useRequireRole } from "@/lib/useRequireRole";
import type { Course, StudyPlan } from "@/types";

const isoPlus = (d: number) => new Date(Date.now() + d * 86400000).toISOString().slice(0, 10);

export default function PlannerPage() {
  const ok = useRequireRole(["student"]);
  const [courses, setCourses] = useState<Course[] | null>(null);
  const [courseId, setCourseId] = useState("");
  const [exam, setExam] = useState(isoPlus(14));
  const [minutes, setMinutes] = useState("45");
  const [plan, setPlan] = useState<StudyPlan | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!ok) return;
    api.get<Course[]>("/courses/mine").then((c) => { setCourses(c); if (c[0]) setCourseId(String(c[0].id)); }).catch(() => setCourses([]));
  }, [ok]);

  async function build(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setBusy(true);
    try {
      setPlan(await api.post<StudyPlan>("/planner", { course_id: Number(courseId), exam_date: exam, minutes_per_day: Number(minutes) }));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not build a plan.");
    } finally {
      setBusy(false);
    }
  }

  if (!ok) return null;
  return (
    <div className="space-y-6">
      <div>
        <p className="text-sm font-semibold text-brand-600">Revision planner</p>
        <h1 className="mt-1 font-display text-3xl font-extrabold tracking-tight text-ink">Plan your revision</h1>
        <p className="mt-1 text-sm text-muted">Weak topics are scheduled first, then anything you haven&apos;t finished.</p>
      </div>

      {courses && courses.length === 0 ? (
        <EmptyState icon={<CalendarDays className="h-5 w-5" />} title="Enrol in a course first" description="The planner needs a course to build a schedule from." action={<Link href="/courses" className="font-semibold text-brand-600">Browse courses</Link>} />
      ) : (
        <Card className="p-5 sm:p-6">
          <form onSubmit={build} className="grid gap-4 sm:grid-cols-4 sm:items-end">
            <Select label="Course" value={courseId} onChange={(e) => setCourseId(e.target.value)}>
              {(courses ?? []).map((c) => <option key={c.id} value={c.id}>{c.title}</option>)}
            </Select>
            <Input label="Exam date" name="exam" type="date" min={isoPlus(1)} value={exam} onChange={(e) => setExam(e.target.value)} required />
            <Select label="Study time per day" value={minutes} onChange={(e) => setMinutes(e.target.value)}>
              {[20, 30, 45, 60, 90, 120].map((m) => <option key={m} value={m}>{m} minutes</option>)}
            </Select>
            <Button type="submit" loading={busy} disabled={!courseId}>Build my plan</Button>
          </form>
          {error && <p className="mt-3 rounded-xl bg-rose-50 px-4 py-2.5 text-sm font-medium text-rose-700">{error}</p>}
        </Card>
      )}

      {plan && (
        <div className="space-y-4">
          <div className="flex flex-wrap gap-2 text-sm">
            <Badge tone="blue"><Clock className="h-3.5 w-3.5" /> {Math.round(plan.total_minutes / 60 * 10) / 10} h total</Badge>
            {plan.weak_topics.map((t) => <Badge key={t} tone="rose">Weak: {t}</Badge>)}
            {plan.unscheduled > 0 && <Badge tone="amber">{plan.unscheduled} lessons won&apos;t fit — increase daily time</Badge>}
          </div>
          {plan.days.length === 0 && <EmptyState icon={<CalendarDays className="h-5 w-5" />} title="Nothing left to revise 🎉" description="You've completed everything in this course." />}
          {plan.days.map((d, i) => (
            <Card key={d.date} className="p-4 sm:p-5">
              <div className="flex items-center justify-between">
                <p className="font-display font-bold text-ink">Day {i + 1} · {new Date(d.date + "T00:00").toLocaleDateString(undefined, { weekday: "short", month: "short", day: "numeric" })}</p>
                <span className="text-xs font-semibold text-muted">{d.total_minutes} min</span>
              </div>
              <div className="mt-3 divide-y divide-line/70">
                {d.items.map((it) => (
                  <Link key={it.lesson_id} href={`/lessons/${it.lesson_id}`} className="flex min-h-[52px] items-center gap-3 py-2.5">
                    <span className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-xl ${it.kind === "revise" ? "bg-rose-50 text-rose-600" : "bg-brand-50 text-brand-600"}`}>
                      {it.kind === "revise" ? <RotateCcw className="h-4 w-4" /> : <CalendarDays className="h-4 w-4" />}
                    </span>
                    <span className="min-w-0 flex-1"><span className="block truncate text-sm font-semibold text-ink">{it.title}</span><span className="block truncate text-xs text-muted">{it.topic} · {it.reason}</span></span>
                    <span className="text-xs text-muted">{it.minutes}m</span>
                  </Link>
                ))}
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
