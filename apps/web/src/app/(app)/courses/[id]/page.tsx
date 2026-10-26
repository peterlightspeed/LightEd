"use client";

/**
 * Course detail page.
 *
 * Shows the course hero, an accordion of topics -> lessons, and an enrol CTA.
 * Lesson rows link straight into the lesson viewer.
 */
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import {
  ArrowLeft,
  BookOpen,
  CheckCircle2,
  ChevronDown,
  Clock,
  GraduationCap,
  Layers,
  PlayCircle,
} from "lucide-react";

import { Badge, Button, ButtonLink, Card, EmptyState, ProgressBar, Skeleton } from "@/components/ui";
import { api } from "@/lib/api";
import { accent } from "@/lib/utils";
import type { CourseDetail } from "@/types";

export default function CourseDetailPage() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const [course, setCourse] = useState<CourseDetail | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [enrolling, setEnrolling] = useState(false);
  const [openTopics, setOpenTopics] = useState<Record<number, boolean>>({});

  async function load() {
    try {
      const data = await api.get<CourseDetail>(`/courses/${params.id}`);
      setCourse(data);
      // Open the first topic by default so the page never looks empty.
      if (data.topics.length > 0) {
        setOpenTopics((prev) => (Object.keys(prev).length ? prev : { [data.topics[0].id]: true }));
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not load this course.");
    }
  }

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [params.id]);

  async function enroll() {
    setEnrolling(true);
    try {
      await api.post(`/courses/${params.id}/enroll`, {});
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not enrol in this course.");
    } finally {
      setEnrolling(false);
    }
  }

  if (error) {
    return (
      <EmptyState
        icon={<BookOpen className="h-5 w-5" />}
        title="Course not found"
        description={error}
        action={<ButtonLink href="/courses">Back to courses</ButtonLink>}
      />
    );
  }

  if (!course) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-52 w-full" />
        <Skeleton className="h-80 w-full" />
      </div>
    );
  }

  const tone = accent(course.accent);
  const firstLesson = course.topics.flatMap((t) => t.lessons)[0];
  const completed = course.topics.flatMap((t) => t.lessons).filter((l) => l.completed).length;

  return (
    <div className="space-y-7">
      <button
        onClick={() => router.push("/courses")}
        className="inline-flex items-center gap-2 text-sm font-semibold text-muted hover:text-ink"
      >
        <ArrowLeft className="h-4 w-4" />
        All courses
      </button>

      {/* Hero */}
      <Card className={`overflow-hidden border-0 bg-gradient-to-br ${tone.bg} p-0 text-white`}>
        <div className="relative p-7 sm:p-10">
          <div className="pointer-events-none absolute -right-10 -top-10 h-48 w-48 rounded-full bg-white/10 blur-2xl" />
          <div className="flex flex-wrap items-center gap-2">
            <span className="rounded-full bg-white/20 px-3 py-1 text-xs font-semibold backdrop-blur">{course.subject}</span>
            <span className="rounded-full bg-white/20 px-3 py-1 text-xs font-semibold backdrop-blur">{course.level}</span>
            {course.enrolled && (
              <span className="inline-flex items-center gap-1 rounded-full bg-white px-3 py-1 text-xs font-bold text-navy-700">
                <CheckCircle2 className="h-3.5 w-3.5" />
                Enrolled
              </span>
            )}
          </div>
          <h1 className="mt-4 max-w-2xl font-display text-3xl font-extrabold tracking-tight sm:text-4xl">
            {course.title}
          </h1>
          <p className="mt-3 max-w-2xl text-sm leading-6 text-white/80">{course.description}</p>

          <div className="mt-6 flex flex-wrap items-center gap-x-6 gap-y-2 text-sm text-white/80">
            <span className="inline-flex items-center gap-2">
              <BookOpen className="h-4 w-4" /> {course.lesson_count} lessons
            </span>
            <span className="inline-flex items-center gap-2">
              <Layers className="h-4 w-4" /> {course.topic_count} topics
            </span>
            <span className="inline-flex items-center gap-2">
              <GraduationCap className="h-4 w-4" /> {course.owner_name}
            </span>
          </div>

          <div className="mt-7 flex flex-wrap gap-3">
            {course.enrolled ? (
              firstLesson && (
                <ButtonLink href={`/lessons/${firstLesson.id}`} variant="gold" size="lg">
                  <PlayCircle className="h-4 w-4" />
                  {completed > 0 ? "Continue course" : "Start course"}
                </ButtonLink>
              )
            ) : (
              <Button variant="gold" size="lg" loading={enrolling} onClick={enroll}>
                Enrol for free
              </Button>
            )}
          </div>
        </div>
      </Card>

      {course.enrolled && (
        <Card>
          <div className="flex items-center justify-between text-sm">
            <span className="font-semibold text-ink">Your progress</span>
            <span className="text-muted">
              {completed}/{course.lesson_count} lessons · {Math.round(course.progress)}%
            </span>
          </div>
          <ProgressBar value={course.progress} className="mt-2" barClassName={tone.solid} />
        </Card>
      )}

      {/* Curriculum */}
      <div className="grid gap-6 lg:grid-cols-[1fr_320px]">
        <Card>
          <h2 className="font-display text-lg font-bold text-ink">Curriculum</h2>
          <p className="mt-1 text-sm text-muted">Work through topics in order, or jump to any lesson.</p>

          <div className="mt-5 space-y-3">
            {course.topics.map((topic, index) => {
              const open = openTopics[topic.id];
              return (
                <div key={topic.id} className="overflow-hidden rounded-2xl border border-line/70">
                  <button
                    onClick={() => setOpenTopics((prev) => ({ ...prev, [topic.id]: !prev[topic.id] }))}
                    className="flex w-full items-center justify-between gap-3 bg-mist/50 px-4 py-3 text-left transition hover:bg-mist"
                  >
                    <span className="flex items-center gap-3">
                      <span className="flex h-7 w-7 items-center justify-center rounded-lg bg-navy-700 text-xs font-bold text-white">
                        {index + 1}
                      </span>
                      <span>
                        <span className="block text-sm font-semibold text-ink">{topic.title}</span>
                        <span className="block text-[11px] text-muted">{topic.lessons.length} lessons</span>
                      </span>
                    </span>
                    <ChevronDown className={`h-4 w-4 text-muted transition ${open ? "rotate-180" : ""}`} />
                  </button>

                  {open && (
                    <ul className="divide-y divide-line/60">
                      {topic.lessons.map((lesson) => (
                        <li key={lesson.id}>
                          <Link
                            href={`/lessons/${lesson.id}`}
                            className="flex items-center gap-3 px-4 py-3 transition hover:bg-mist/40"
                          >
                            <span
                              className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-full ${
                                lesson.completed ? "bg-emerald-50 text-emerald-600" : "bg-navy-50 text-navy-700"
                              }`}
                            >
                              {lesson.completed ? <CheckCircle2 className="h-4 w-4" /> : <PlayCircle className="h-4 w-4" />}
                            </span>
                            <span className="min-w-0 flex-1">
                              <span className="block truncate text-sm font-medium text-ink">{lesson.title}</span>
                              <span className="block text-[11px] text-muted">{lesson.summary}</span>
                            </span>
                            <span className="inline-flex shrink-0 items-center gap-1 text-[11px] text-muted">
                              <Clock className="h-3.5 w-3.5" />
                              {lesson.duration_minutes}m
                            </span>
                          </Link>
                        </li>
                      ))}
                    </ul>
                  )}
                </div>
              );
            })}
          </div>
        </Card>

        {/* Sidebar */}
        <div className="space-y-5">
          <Card>
            <h3 className="font-display text-base font-bold text-ink">What you&apos;ll learn</h3>
            <ul className="mt-3 space-y-2 text-sm text-muted">
              {[
                "Core concepts broken into short lessons",
                "A quick quiz after each lesson",
                "Progress saved automatically",
              ].map((item) => (
                <li key={item} className="flex items-start gap-2">
                  <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-emerald-500" />
                  {item}
                </li>
              ))}
            </ul>
          </Card>

          <Card className="bg-navy-700 text-white">
            <h3 className="font-display text-base font-bold">Need a hand?</h3>
            <p className="mt-1 text-sm text-white/70">
              Open any lesson and ask the AI tutor to explain a step in plain language.
            </p>
            <Badge tone="amber" className="mt-3">Included free</Badge>
          </Card>
        </div>
      </div>
    </div>
  );
}
