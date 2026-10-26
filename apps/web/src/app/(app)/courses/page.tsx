"use client";

/**
 * Course catalogue.
 *
 * Fetches /courses (personalised when signed in) and filters client-side by
 * search text, subject, and level. Kept simple on purpose: the dataset is small
 * and this avoids extra round-trips.
 */
import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { ArrowRight, BookOpen, Filter, Search, Sparkles } from "lucide-react";

import { Badge, ButtonLink, Card, EmptyState, Input, ProgressBar, Select, Skeleton } from "@/components/ui";
import { api } from "@/lib/api";
import { accent } from "@/lib/utils";
import type { Course } from "@/types";

export default function CoursesPage() {
  const [courses, setCourses] = useState<Course[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [query, setQuery] = useState("");
  const [subject, setSubject] = useState("all");
  const [level, setLevel] = useState("all");

  useEffect(() => {
    api
      .get<Course[]>("/courses")
      .then(setCourses)
      .catch((err) => setError(err instanceof Error ? err.message : "Could not load courses."));
  }, []);

  const subjects = useMemo(
    () => Array.from(new Set((courses ?? []).map((c) => c.subject))).sort(),
    [courses]
  );
  const levels = useMemo(
    () => Array.from(new Set((courses ?? []).map((c) => c.level))).sort(),
    [courses]
  );

  const filtered = useMemo(() => {
    return (courses ?? []).filter((course) => {
      const matchesQuery =
        !query ||
        course.title.toLowerCase().includes(query.toLowerCase()) ||
        course.description.toLowerCase().includes(query.toLowerCase());
      const matchesSubject = subject === "all" || course.subject === subject;
      const matchesLevel = level === "all" || course.level === level;
      return matchesQuery && matchesSubject && matchesLevel;
    });
  }, [courses, query, subject, level]);

  return (
    <div className="space-y-7">
      <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-end">
        <div>
          <p className="text-sm font-semibold text-brand-600">Catalogue</p>
          <h1 className="mt-1 font-display text-3xl font-extrabold tracking-tight text-ink">Explore courses</h1>
          <p className="mt-1 text-sm text-muted">
            Structured paths in maths, science, history, and programming.
          </p>
        </div>
        <ButtonLink href="/progress" variant="secondary">
          <Sparkles className="h-4 w-4" />
          My progress
        </ButtonLink>
      </div>

      {/* Filters */}
      <Card className="p-4">
        <div className="grid gap-3 sm:grid-cols-[1fr_180px_180px]">
          <Input
            placeholder="Search courses…"
            icon={<Search className="h-4 w-4" />}
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
          <Select value={subject} onChange={(e) => setSubject(e.target.value)} aria-label="Filter by subject">
            <option value="all">All subjects</option>
            {subjects.map((s) => (
              <option key={s} value={s}>
                {s}
              </option>
            ))}
          </Select>
          <Select value={level} onChange={(e) => setLevel(e.target.value)} aria-label="Filter by level">
            <option value="all">All levels</option>
            {levels.map((l) => (
              <option key={l} value={l}>
                {l}
              </option>
            ))}
          </Select>
        </div>
        <div className="mt-3 flex items-center gap-2 text-xs text-muted">
          <Filter className="h-3.5 w-3.5" />
          {filtered.length} course{filtered.length === 1 ? "" : "s"} shown
        </div>
      </Card>

      {error && <EmptyState title="Could not load courses" description={error} />}

      {!courses && !error && (
        <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 6 }).map((_, i) => (
            <Skeleton key={i} className="h-56" />
          ))}
        </div>
      )}

      {courses && filtered.length === 0 && (
        <EmptyState
          icon={<BookOpen className="h-5 w-5" />}
          title="No courses match those filters"
          description="Try clearing the search or picking a different subject."
        />
      )}

      <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
        {filtered.map((course) => {
          const tone = accent(course.accent);
          return (
            <Link key={course.id} href={`/courses/${course.id}`} className="group">
              <Card className="flex h-full flex-col overflow-hidden p-0 transition group-hover:-translate-y-1 group-hover:shadow-float">
                <div className={`relative h-28 bg-gradient-to-br ${tone.bg} p-5`}>
                  <span className="inline-flex items-center gap-1.5 rounded-full bg-white/20 px-2.5 py-1 text-xs font-semibold text-white backdrop-blur">
                    {course.subject}
                  </span>
                  <div className="absolute -bottom-6 right-5 flex h-12 w-12 items-center justify-center rounded-2xl bg-white text-navy-700 shadow-card">
                    <BookOpen className="h-6 w-6" />
                  </div>
                </div>
                <div className="flex flex-1 flex-col p-5 pt-7">
                  <div className="flex items-center gap-2">
                    <Badge tone="neutral">{course.level}</Badge>
                    {course.enrolled && <Badge tone="blue">Enrolled</Badge>}
                  </div>
                  <h3 className="mt-3 font-display text-lg font-bold text-ink group-hover:text-brand-700">
                    {course.title}
                  </h3>
                  <p className="mt-1 line-clamp-2 text-sm text-muted">{course.description}</p>

                  <div className="mt-auto pt-5">
                    {course.enrolled ? (
                      <>
                        <div className="flex items-center justify-between text-xs text-muted">
                          <span>Progress</span>
                          <span className="font-semibold text-ink">{Math.round(course.progress)}%</span>
                        </div>
                        <ProgressBar value={course.progress} size="sm" className="mt-1.5" barClassName={tone.solid} />
                      </>
                    ) : (
                      <div className="flex items-center justify-between text-xs text-muted">
                        <span>
                          {course.lesson_count} lessons · {course.topic_count} topics
                        </span>
                        <span className="inline-flex items-center gap-1 font-semibold text-brand-600">
                          View
                          <ArrowRight className="h-3.5 w-3.5" />
                        </span>
                      </div>
                    )}
                  </div>
                </div>
              </Card>
            </Link>
          );
        })}
      </div>
    </div>
  );
}
