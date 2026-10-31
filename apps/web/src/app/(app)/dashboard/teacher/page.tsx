"use client";

/**
 * Teacher dashboard.
 *
 * Shows aggregate class stats, per-course progress, and a roster with an
 * "at risk" flag derived from average quiz scores on the backend.
 */
import Link from "next/link";
import UpcomingSessions from "@/components/live/UpcomingSessions";
import CourseIdeas from "@/components/teacher/CourseIdeas";
import TeacherGuide from "@/components/teacher/TeacherGuide";
import { greetingFor } from "@/lib/utils";
import { useEffect, useState } from "react";
import {
  AlertTriangle,
  ArrowRight,
  BookOpen,
  GraduationCap,
  TrendingUp,
  Users,
} from "lucide-react";

import {
  Avatar,
  Badge,
  ButtonLink,
  Card,
  CardHeader,
  EmptyState,
  ProgressBar,
  Skeleton,
} from "@/components/ui";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";
import { accent } from "@/lib/utils";
import type { TeacherDashboard } from "@/types";

export default function TeacherDashboardPage() {
  const { user } = useAuth();
  const [data, setData] = useState<TeacherDashboard | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .get<TeacherDashboard>("/dashboard/teacher")
      .then(setData)
      .catch((err) => setError(err instanceof Error ? err.message : "Could not load the class dashboard."));
  }, []);

  if (error) {
    return <EmptyState icon={<Users className="h-5 w-5" />} title="Dashboard unavailable" description={error} />;
  }

  if (!data) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-24 w-full" />
        <div className="grid grid-cols-2 gap-3 sm:gap-4 lg:grid-cols-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <Skeleton key={i} className="h-28" />
          ))}
        </div>
        <Skeleton className="h-72 w-full" />
      </div>
    );
  }

  const { stats, courses, students } = data;
  const atRisk = students.filter((s) => s.status === "at_risk");

  const statCards = [
    { label: "Total students", value: stats.total_students, icon: Users, tone: "bg-brand-50 text-brand-600" },
    { label: "Active courses", value: stats.active_courses, icon: BookOpen, tone: "bg-emerald-50 text-emerald-600" },
    { label: "Class average", value: `${Math.round(stats.avg_score)}%`, icon: TrendingUp, tone: "bg-amber-50 text-amber-600" },
    { label: "At risk", value: stats.at_risk, icon: AlertTriangle, tone: "bg-rose-50 text-rose-600" },
  ];

  return (
    <div className="space-y-7">
      <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-end">
        <div>
          <p className="text-sm font-semibold text-brand-600">Teacher workspace</p>
          <h1 className="mt-1 font-display text-3xl font-extrabold tracking-tight text-ink">
            {greetingFor(user ?? data.user)}
          </h1>
          <p className="mt-1 text-sm text-muted">
            Here&apos;s how your classes are doing this week.
          </p>
        </div>
        <ButtonLink href="/courses">
          <BookOpen className="h-4 w-4" />
          Manage courses
        </ButtonLink>
      </div>

      <TeacherGuide />

      {/* Stat cards */}
      <div className="grid grid-cols-2 gap-3 sm:gap-4 lg:grid-cols-4">
        {statCards.map((card) => {
          const Icon = card.icon;
          return (
            <Card key={card.label} className="p-5">
              <span className={`flex h-11 w-11 items-center justify-center rounded-2xl ${card.tone}`}>
                <Icon className="h-5 w-5" />
              </span>
              <p className="mt-4 font-display text-2xl font-extrabold text-ink">{card.value}</p>
              <p className="text-sm text-muted">{card.label}</p>
            </Card>
          );
        })}
      </div>

      <CourseIdeas />

      <UpcomingSessions />

      <div className="grid gap-6 lg:grid-cols-3">
        {/* Course progress */}
        <Card className="lg:col-span-2 min-w-0">
          <CardHeader
            title="Course progress"
            subtitle="Average completion across enrolled students."
            action={
              <Link href="/courses" className="text-sm font-semibold text-brand-600 hover:text-brand-700">
                All courses
              </Link>
            }
          />
          <div className="mt-5 space-y-4">
            {courses.length === 0 && (
              <EmptyState
                title="No courses yet"
                description="Create your first course to start tracking a class."
                action={<ButtonLink href="/courses">Go to courses</ButtonLink>}
              />
            )}
            {courses.map((course) => {
              const tone = accent(course.accent);
              return (
                <Link
                  key={course.id}
                  href={`/courses/${course.id}`}
                  className="block rounded-2xl border border-line/70 p-4 transition hover:border-brand-300 hover:bg-mist/40"
                >
                  <div className="flex items-center justify-between gap-3">
                    <div className="flex items-center gap-3">
                      <span className={`flex h-10 w-10 items-center justify-center rounded-xl ${tone.soft} ${tone.text}`}>
                        <BookOpen className="h-5 w-5" />
                      </span>
                      <div>
                        <p className="font-semibold text-ink">{course.title}</p>
                        <p className="text-xs text-muted">
                          {course.students} students · {course.lessons} lessons · {course.subject}
                        </p>
                      </div>
                    </div>
                    <span className="text-sm font-semibold text-muted">{Math.round(course.avg_progress)}%</span>
                  </div>
                  <ProgressBar value={course.avg_progress} size="sm" className="mt-3" barClassName={tone.solid} />
                </Link>
              );
            })}
          </div>
        </Card>

        {/* At-risk students */}
        <Card>
          <CardHeader
            title="Needs attention"
            subtitle="Students with an average below 60%."
            action={<AlertTriangle className="h-5 w-5 text-rose-500" />}
          />
          <div className="mt-5 space-y-4">
            {atRisk.length === 0 && (
              <div className="rounded-2xl bg-emerald-50 p-4 text-sm text-emerald-700">
                Everyone is on track right now. 🎉
              </div>
            )}
            {atRisk.map((student) => (
              <div key={student.id} className="flex items-center gap-3">
                <Avatar name={student.name} size="sm" />
                <div className="min-w-0 flex-1">
                  <p className="truncate text-sm font-semibold text-ink">{student.name}</p>
                  <p className="text-[11px] text-muted">{student.lessons_completed} lessons completed</p>
                </div>
                <Badge tone="rose">{Math.round(student.avg_score)}%</Badge>
              </div>
            ))}
          </div>
        </Card>
      </div>

      {/* Full roster */}
      <Card>
        <CardHeader
          title="Student roster"
          subtitle={`${students.length} learners across your courses.`}
          action={
            <span className="inline-flex items-center gap-1.5 text-xs font-semibold text-muted">
              <GraduationCap className="h-4 w-4" />
              Live from quiz activity
            </span>
          }
        />
        {/* Phones: tappable cards (no sideways scrolling). */}
        <div className="mt-4 divide-y divide-line/70 md:hidden">
          {students.map((student) => (
            <Link key={student.id} href={`/students/${student.id}`} className="flex min-h-[64px] items-center gap-3 py-3">
              <Avatar name={student.name} size="sm" />
              <div className="min-w-0 flex-1">
                <p className="truncate font-semibold text-ink">{student.name}</p>
                <p className="text-xs text-muted">{Math.round(student.avg_score)}% avg · {student.lessons_completed} lessons</p>
              </div>
              <Badge tone={student.status === "at_risk" ? "rose" : "green"}>
                {student.status === "at_risk" ? "At risk" : "On track"}
              </Badge>
            </Link>
          ))}
        </div>
        <div className="mt-4 hidden overflow-x-auto md:block">
          <table className="w-full min-w-[560px] text-left text-sm">
            <thead>
              <tr className="border-b border-line text-xs uppercase tracking-wide text-muted">
                <th className="pb-3 font-semibold">Student</th>
                <th className="pb-3 font-semibold">Avg score</th>
                <th className="pb-3 font-semibold">Lessons</th>
                <th className="pb-3 font-semibold">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-line/70">
              {students.map((student) => (
                <tr key={student.id} className="hover:bg-mist/40">
                  <td className="py-3">
                    <div className="flex items-center gap-3">
                      <Avatar name={student.name} size="sm" />
                      <div>
                        <p className="font-semibold text-ink">{student.name}</p>
                        <p className="text-[11px] text-muted">{student.email}</p>
                      </div>
                    </div>
                  </td>
                  <td className="py-3 font-medium text-ink">{Math.round(student.avg_score)}%</td>
                  <td className="py-3 text-muted">{student.lessons_completed}</td>
                  <td className="py-3">
                    <Badge tone={student.status === "at_risk" ? "rose" : "green"}>
                      {student.status === "at_risk" ? "At risk" : "On track"}
                    </Badge>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>

      <div className="flex justify-end">
        <Link href="/courses" className="inline-flex items-center gap-2 text-sm font-semibold text-brand-600 hover:text-brand-700">
          Create a new course
          <ArrowRight className="h-4 w-4" />
        </Link>
      </div>
    </div>
  );
}
