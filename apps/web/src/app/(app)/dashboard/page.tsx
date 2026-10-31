"use client";

/**
 * Student dashboard.
 *
 * Pulls everything from a single endpoint (/dashboard/student) so the page
 * renders in one round-trip: stats, continue-learning, course progress,
 * focus areas, recommendations, recent quiz attempts and weekly activity.
 */
import Link from "next/link";
import UpcomingSessions from "@/components/live/UpcomingSessions";
import { greetingFor } from "@/lib/utils";
import { useEffect, useState } from "react";
import {
  ArrowRight,
  BookOpen,
  CalendarDays,
  Flame,
  PlayCircle,
  Sparkles,
  Target,
  TrendingUp,
  Trophy,
} from "lucide-react";

import {
  Badge,
  ButtonLink,
  Card,
  CardHeader,
  EmptyState,
  PageLoader,
  ProgressBar,
  ProgressRing,
  Skeleton,
} from "@/components/ui";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";
import { accent, formatDate } from "@/lib/utils";
import type { StudentDashboard } from "@/types";

export default function StudentDashboardPage() {
  const { user } = useAuth();
  const [data, setData] = useState<StudentDashboard | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .get<StudentDashboard>("/dashboard/student")
      .then(setData)
      .catch((err) => setError(err instanceof Error ? err.message : "Could not load your dashboard."));
  }, []);

  if (error) {
    return (
      <EmptyState
        icon={<BookOpen className="h-5 w-5" />}
        title="We couldn't load your dashboard"
        description={error}
        action={<ButtonLink href="/courses">Browse courses</ButtonLink>}
      />
    );
  }

  if (!data) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-28 w-full" />
        <div className="grid gap-6 lg:grid-cols-3">
          <Skeleton className="h-64 lg:col-span-2" />
          <Skeleton className="h-64" />
        </div>
        <PageLoader label="Loading your progress" />
      </div>
    );
  }

  const { stats, continue_learning, courses, focus_areas, recommendations, recent_attempts, weekly_activity } = data;
  const maxActivity = Math.max(1, ...weekly_activity.map((d) => d.lessons));

  return (
    <div className="space-y-7">
      {/* ---------------------------------------------------------- Header */}
      <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-end">
        <div>
          <p className="text-sm font-semibold text-brand-600">Your learning overview</p>
          <h1 className="mt-1 font-display text-3xl font-extrabold tracking-tight text-ink">
            {greetingFor(user ?? data.user)}
          </h1>
          <p className="mt-1 text-sm text-muted">
            You&apos;ve completed {stats.lessons_completed} of {stats.lessons_total} lessons. Keep the streak alive.
          </p>
        </div>
        <div className="grid grid-cols-1 gap-3 min-[360px]:grid-cols-2 sm:flex">
          <ButtonLink href="/courses" variant="secondary" className="whitespace-nowrap [&>svg]:hidden sm:[&>svg]:block">
            <BookOpen className="h-4 w-4" />
            Browse courses
          </ButtonLink>
          {continue_learning && (
            <ButtonLink href={`/lessons/${continue_learning.lesson_id}`} className="whitespace-nowrap [&>svg]:hidden sm:[&>svg]:block">
              <PlayCircle className="h-4 w-4" />
              Continue learning
            </ButtonLink>
          )}
        </div>
      </div>

      {/* ------------------------------------------------- Stat + progress */}
      <UpcomingSessions />

      <div className="grid gap-6 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <div className="flex flex-col gap-6 sm:flex-row sm:items-center">
            <ProgressRing
              value={Math.round((stats.lessons_completed / Math.max(1, stats.lessons_total)) * 100)}
              size={148}
              sublabel="overall"
            />
            <div className="flex-1">
              <div className="flex items-center justify-between">
                <h2 className="font-display text-lg font-bold text-ink">Overall progress</h2>
                <Badge tone="green">
                  <TrendingUp className="h-3.5 w-3.5" />
                  On track
                </Badge>
              </div>
              <p className="mt-1 text-sm text-muted">
                {stats.lessons_completed} of {stats.lessons_total} lessons complete across {stats.enrolled_courses} courses.
              </p>
              <div className="mt-5 grid grid-cols-3 gap-3">
                {[
                  { label: "Courses", value: stats.enrolled_courses, icon: BookOpen },
                  { label: "Avg score", value: `${Math.round(stats.avg_score)}%`, icon: Trophy },
                  { label: "Streak", value: `${stats.streak_days}d`, icon: Flame },
                ].map((item) => {
                  const Icon = item.icon;
                  return (
                    <div key={item.label} className="rounded-2xl bg-mist p-3">
                      <Icon className="h-4 w-4 text-brand-500" />
                      <p className="mt-2 font-display text-lg font-extrabold text-ink">{item.value}</p>
                      <p className="text-[11px] font-medium text-muted">{item.label}</p>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        </Card>

        {/* Continue learning card */}
        <Card className="flex flex-col justify-between bg-navy-700 text-white">
          <div>
            <div className="flex items-center gap-2 text-gold-300">
              <PlayCircle className="h-4 w-4" />
              <span className="text-xs font-bold uppercase tracking-wide">Pick up where you left off</span>
            </div>
            {continue_learning ? (
              <>
                <h3 className="mt-3 font-display text-xl font-bold">{continue_learning.lesson_title}</h3>
                <p className="mt-1 text-sm text-white/60">
                  {continue_learning.course_title} · {continue_learning.topic_title}
                </p>
                <div className="mt-4">
                  <div className="flex justify-between text-xs text-white/60">
                    <span>Course progress</span>
                    <span>{Math.round(continue_learning.progress)}%</span>
                  </div>
                  <div className="mt-1.5 h-2 overflow-hidden rounded-full bg-white/15">
                    <div
                      className="h-full rounded-full bg-gold-400"
                      style={{ width: `${Math.min(100, continue_learning.progress)}%` }}
                    />
                  </div>
                </div>
              </>
            ) : (
              <p className="mt-3 text-sm text-white/70">
                You&apos;re all caught up. Enrol in a new course to keep going.
              </p>
            )}
          </div>
          <Link
            href={continue_learning ? `/lessons/${continue_learning.lesson_id}` : "/courses"}
            className="mt-6 inline-flex items-center gap-2 text-sm font-semibold text-gold-300 hover:text-gold-200"
          >
            {continue_learning ? "Resume lesson" : "Find a course"}
            <ArrowRight className="h-4 w-4" />
          </Link>
        </Card>
      </div>

      {/* --------------------------------------------- Courses + side rail */}
      <div className="grid gap-6 lg:grid-cols-3">
        <div className="min-w-0 space-y-6 lg:col-span-2">
          <Card>
            <CardHeader
              title="Your courses"
              subtitle="Progress is based on completed lessons."
              action={
                <Link href="/courses" className="text-sm font-semibold text-brand-600 hover:text-brand-700">
                  View all
                </Link>
              }
            />
            <div className="mt-5 space-y-3">
              {courses.length === 0 && (
                <EmptyState
                  title="No courses yet"
                  description="Enrol in your first course to start tracking progress."
                  action={<ButtonLink href="/courses">Browse courses</ButtonLink>}
                />
              )}
              {courses.map((course) => {
                const tone = accent(course.accent);
                return (
                  <Link
                    key={course.id}
                    href={`/courses/${course.id}`}
                    className="flex items-center gap-4 rounded-2xl border border-line/70 p-4 transition hover:border-brand-300 hover:bg-mist/50"
                  >
                    <span className={`flex h-12 w-12 shrink-0 items-center justify-center rounded-xl ${tone.soft} ${tone.text}`}>
                      <BookOpen className="h-5 w-5" />
                    </span>
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center justify-between gap-3">
                        <p className="truncate font-semibold text-ink">{course.title}</p>
                        <span className="shrink-0 text-xs font-semibold text-muted">{Math.round(course.progress)}%</span>
                      </div>
                      <p className="text-xs text-muted">
                        {course.lessons_completed}/{course.lesson_count} lessons · {course.subject}
                      </p>
                      <ProgressBar value={course.progress} size="sm" className="mt-2" barClassName={tone.solid} />
                    </div>
                  </Link>
                );
              })}
            </div>
          </Card>

          {/* Weekly activity bar chart (pure CSS, no chart library). */}
          <Card>
            <CardHeader title="This week" subtitle="Lessons completed each day." />
            <div className="mt-6 flex items-end justify-between gap-2 sm:gap-4">
              {weekly_activity.map((day) => (
                <div key={day.day} className="flex flex-1 flex-col items-center gap-2">
                  <span className="text-[11px] font-semibold text-muted">{day.lessons}</span>
                  <div className="flex h-32 w-full items-end rounded-xl bg-mist">
                    <div
                      className="w-full rounded-xl bg-gradient-to-t from-brand-600 to-brand-400 transition-all"
                      style={{ height: `${Math.max(6, (day.lessons / maxActivity) * 100)}%` }}
                    />
                  </div>
                  <span className="text-[11px] font-medium text-muted">{day.day}</span>
                </div>
              ))}
            </div>
          </Card>
        </div>

        <div className="space-y-6">
          {/* Focus areas */}
          <Card>
            <CardHeader title="Focus areas" subtitle="Where a little review helps most." />
            <div className="mt-5 space-y-4">
              {focus_areas.length === 0 && <p className="text-sm text-muted">Nothing flagged — nice work.</p>}
              {focus_areas.map((area) => (
                <div key={area.course_id}>
                  <div className="flex items-center justify-between text-sm">
                    <span className="font-medium text-ink">{area.label}</span>
                    <span className="text-xs text-muted">{Math.round(area.mastery)}%</span>
                  </div>
                  <ProgressBar
                    value={area.mastery}
                    size="sm"
                    className="mt-1.5"
                    barClassName={area.mastery < 50 ? "bg-rose-500" : area.mastery < 75 ? "bg-amber-500" : "bg-emerald-500"}
                  />
                </div>
              ))}
            </div>
          </Card>

          {/* AI tutor promo */}
          <Card className="bg-gradient-to-br from-brand-500 to-brand-700 text-white">
            <div className="flex items-center gap-2 text-gold-300">
              <Sparkles className="h-4 w-4" />
              <span className="text-xs font-bold uppercase tracking-wide">AI Tutor</span>
            </div>
            <h3 className="mt-3 font-display text-lg font-bold">Stuck on something?</h3>
            <p className="mt-1 text-sm text-white/75">
              Ask for a simpler explanation of any lesson and get a step-by-step walkthrough.
            </p>
            <ButtonLink href="/courses" variant="gold" size="sm" className="mt-4">
              Try it on a lesson
            </ButtonLink>
          </Card>

          {/* Recent attempts */}
          <Card>
            <CardHeader title="Recent quizzes" />
            <div className="mt-4 space-y-3">
              {recent_attempts.length === 0 && <p className="text-sm text-muted">No quiz attempts yet.</p>}
              {recent_attempts.slice(0, 4).map((attempt) => (
                <div key={attempt.id} className="flex items-center justify-between gap-3">
                  <div className="min-w-0">
                    <p className="truncate text-sm font-medium text-ink">{attempt.quiz_title}</p>
                    <p className="text-[11px] text-muted">{formatDate(attempt.created_at)}</p>
                  </div>
                  <Badge tone={attempt.score >= 70 ? "green" : attempt.score >= 50 ? "amber" : "rose"}>
                    {Math.round(attempt.score)}%
                  </Badge>
                </div>
              ))}
            </div>
          </Card>
        </div>
      </div>

      {/* Recommendations */}
      <Card>
        <CardHeader
          title="Recommended for you"
          subtitle="Based on the subjects you're already studying."
          action={<Target className="h-5 w-5 text-brand-500" />}
        />
        <div className="mt-5 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {recommendations.length === 0 && (
            <p className="text-sm text-muted">You&apos;re enrolled in everything we have — for now.</p>
          )}
          {recommendations.map((rec) => {
            const tone = accent(rec.accent);
            return (
              <Link
                key={rec.course_id}
                href={`/courses/${rec.course_id}`}
                className="group rounded-2xl border border-line/70 p-4 transition hover:-translate-y-0.5 hover:border-brand-300 hover:shadow-card"
              >
                <div className="flex items-center justify-between">
                  <span className={`flex h-10 w-10 items-center justify-center rounded-xl ${tone.soft} ${tone.text}`}>
                    <CalendarDays className="h-5 w-5" />
                  </span>
                  <Badge tone="neutral">{rec.level}</Badge>
                </div>
                <h3 className="mt-3 font-display text-base font-bold text-ink group-hover:text-brand-700">{rec.title}</h3>
                <p className="mt-1 text-xs text-muted">{rec.reason}</p>
              </Link>
            );
          })}
        </div>
      </Card>
    </div>
  );
}
