"use client";

/**
 * Progress & analytics page.
 *
 * Turns /progress/me into a readable report: an overall ring, per-course bars,
 * headline stats, and a recent-lesson timeline. All charts are CSS-based so the
 * MVP stays dependency-light.
 */
import { useEffect, useState } from "react";
import { BarChart3, CheckCircle2, Clock, Flame, Trophy } from "lucide-react";

import {
  Badge,
  ButtonLink,
  Card,
  CardHeader,
  EmptyState,
  ProgressBar,
  ProgressRing,
  Skeleton,
} from "@/components/ui";
import { api } from "@/lib/api";
import { formatDate } from "@/lib/utils";
import type { ProgressData } from "@/types";

export default function ProgressPage() {
  const [data, setData] = useState<ProgressData | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .get<ProgressData>("/progress/me")
      .then(setData)
      .catch((err) => setError(err instanceof Error ? err.message : "Could not load your progress."));
  }, []);

  if (error) {
    return (
      <EmptyState
        icon={<BarChart3 className="h-5 w-5" />}
        title="Progress unavailable"
        description={error}
        action={<ButtonLink href="/courses">Browse courses</ButtonLink>}
      />
    );
  }

  if (!data) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-24 w-full" />
        <div className="grid gap-6 lg:grid-cols-3">
          <Skeleton className="h-64" />
          <Skeleton className="h-64 lg:col-span-2 min-w-0" />
        </div>
      </div>
    );
  }

  const stats = [
    { label: "Lessons completed", value: `${data.lessons_completed}/${data.lessons_total}`, icon: CheckCircle2, tone: "bg-brand-50 text-brand-600" },
    { label: "Average score", value: `${Math.round(data.avg_score)}%`, icon: Trophy, tone: "bg-amber-50 text-amber-600" },
    { label: "Current streak", value: `${data.streak_days} day${data.streak_days === 1 ? "" : "s"}`, icon: Flame, tone: "bg-rose-50 text-rose-600" },
  ];

  return (
    <div className="space-y-7">
      <div>
        <p className="text-sm font-semibold text-brand-600">Analytics</p>
        <h1 className="mt-1 font-display text-3xl font-extrabold tracking-tight text-ink">Your progress</h1>
        <p className="mt-1 text-sm text-muted">A clear picture of where you are and what to do next.</p>
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        <Card className="flex flex-col items-center justify-center py-8">
          <ProgressRing value={Math.round(data.overall_progress)} size={160} sublabel="overall" />
          <p className="mt-4 text-sm font-semibold text-ink">Overall completion</p>
          <p className="text-xs text-muted">
            {data.lessons_completed} of {data.lessons_total} lessons
          </p>
        </Card>

        <div className="grid gap-4 sm:grid-cols-3 lg:col-span-2 min-w-0 lg:grid-cols-3">
          {stats.map((stat) => {
            const Icon = stat.icon;
            return (
              <Card key={stat.label} className="flex flex-col justify-between p-5">
                <span className={`flex h-11 w-11 items-center justify-center rounded-2xl ${stat.tone}`}>
                  <Icon className="h-5 w-5" />
                </span>
                <div className="mt-4">
                  <p className="font-display text-2xl font-extrabold text-ink">{stat.value}</p>
                  <p className="text-xs font-medium text-muted">{stat.label}</p>
                </div>
              </Card>
            );
          })}

          <Card className="sm:col-span-3 lg:col-span-3">
            <CardHeader title="Course breakdown" subtitle="Completion per enrolled course." />
            <div className="mt-5 space-y-4">
              {data.courses.length === 0 && <p className="text-sm text-muted">Enrol in a course to see a breakdown.</p>}
              {data.courses.map((course) => (
                <div key={course.course_id}>
                  <div className="flex items-center justify-between text-sm">
                    <span className="font-medium text-ink">{course.title}</span>
                    <span className="text-xs text-muted">
                      {course.lessons_completed}/{course.lessons_total} · {Math.round(course.progress)}%
                    </span>
                  </div>
                  <ProgressBar value={course.progress} size="sm" className="mt-1.5" />
                </div>
              ))}
            </div>
          </Card>
        </div>
      </div>

      <Card>
        <CardHeader
          title="Recent lessons"
          subtitle="The last lessons you opened or completed."
          action={<Clock className="h-5 w-5 text-brand-500" />}
        />
        <div className="mt-5 space-y-3">
          {data.recent_lessons.length === 0 && <p className="text-sm text-muted">No lesson activity yet.</p>}
          {data.recent_lessons.map((lesson) => (
            <div
              key={lesson.lesson_id}
              className="flex flex-col justify-between gap-2 rounded-2xl border border-line/70 p-4 sm:flex-row sm:items-center"
            >
              <div className="flex items-center gap-3">
                <span
                  className={`flex h-9 w-9 items-center justify-center rounded-full ${
                    lesson.completed ? "bg-emerald-50 text-emerald-600" : "bg-navy-50 text-navy-700"
                  }`}
                >
                  {lesson.completed ? <CheckCircle2 className="h-4 w-4" /> : <Clock className="h-4 w-4" />}
                </span>
                <div>
                  <p className="text-sm font-semibold text-ink">{lesson.title}</p>
                  <p className="text-[11px] text-muted">{lesson.course_title}</p>
                </div>
              </div>
              <div className="flex items-center gap-3 pl-12 sm:pl-0">
                <Badge tone={lesson.completed ? "green" : "neutral"}>
                  {lesson.completed ? "Completed" : "In progress"}
                </Badge>
                <span className="text-[11px] text-muted">{formatDate(lesson.completed_at)}</span>
              </div>
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
}
