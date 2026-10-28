"use client";

/**
 * Lesson viewer.
 *
 * Renders lesson content (plain paragraphs with **bold** markers), lets the
 * student mark the lesson complete, and links to the quiz + next/prev lessons.
 */
import Link from "next/link";
import Resources from "@/components/lessons/Resources";
import { useParams, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import {
  ArrowLeft,
  ArrowRight,
  CheckCircle2,
  Clock,
  ClipboardCheck,
  Sparkles,
} from "lucide-react";

import { Badge, Button, ButtonLink, Card, EmptyState, Skeleton } from "@/components/ui";
import { api } from "@/lib/api";
import type { LessonDetail } from "@/types";

/**
 * Very small formatter: turns **bold** spans into <strong> and keeps
 * paragraphs separated. Good enough for the seeded lesson copy and avoids
 * pulling in a markdown dependency for the MVP.
 */
function RichText({ text }: { text: string }) {
  return (
    <div className="prose-lesson">
      {text.split(/\n{2,}/).map((block, index) => {
        const isHeading = /^\*\*.+\*\*$/.test(block.trim());
        const parts = block.split(/(\*\*[^*]+\*\*)/g).filter(Boolean);
        const content = parts.map((part, i) =>
          part.startsWith("**") && part.endsWith("**") ? (
            <strong key={i}>{part.slice(2, -2)}</strong>
          ) : (
            <span key={i}>{part}</span>
          )
        );
        return isHeading ? <h3 key={index}>{content}</h3> : <p key={index}>{content}</p>;
      })}
    </div>
  );
}

export default function LessonPage() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const [lesson, setLesson] = useState<LessonDetail | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  async function load() {
    try {
      const data = await api.get<LessonDetail>(`/lessons/${params.id}`);
      setLesson(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not load this lesson.");
    }
  }

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [params.id]);

  async function markComplete() {
    if (!lesson) return;
    setSaving(true);
    try {
      await api.post(`/lessons/${lesson.id}/complete`, {});
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not save your progress.");
    } finally {
      setSaving(false);
    }
  }

  if (error) {
    return (
      <EmptyState
        icon={<ClipboardCheck className="h-5 w-5" />}
        title="Lesson unavailable"
        description={error}
        action={<ButtonLink href="/courses">Back to courses</ButtonLink>}
      />
    );
  }

  if (!lesson) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-10 w-48" />
        <Skeleton className="h-96 w-full" />
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <button
        onClick={() => router.push(`/courses/${lesson.course_id}`)}
        className="inline-flex items-center gap-2 text-sm font-semibold text-muted hover:text-ink"
      >
        <ArrowLeft className="h-4 w-4" />
        {lesson.course_title}
      </button>

      <div>
        <div className="flex flex-wrap items-center gap-2">
          <Badge tone="blue">{lesson.topic_title}</Badge>
          <span className="inline-flex items-center gap-1 text-xs text-muted">
            <Clock className="h-3.5 w-3.5" />
            {lesson.duration_minutes} min read
          </span>
          {lesson.completed && (
            <Badge tone="green">
              <CheckCircle2 className="h-3.5 w-3.5" />
              Completed
            </Badge>
          )}
        </div>
        <h1 className="mt-3 font-display text-3xl font-extrabold tracking-tight text-ink">{lesson.title}</h1>
        <p className="mt-2 text-sm text-muted">{lesson.summary}</p>
      </div>

      <Card className="p-5 sm:p-9">
        <RichText text={lesson.content} />

        {/* AI tutor nudge — the real endpoint is a stub in the MVP. */}
        <div className="mt-8 flex items-start gap-3 rounded-2xl bg-brand-50 p-4">
          <Sparkles className="mt-0.5 h-5 w-5 shrink-0 text-brand-600" />
          <div>
            <p className="text-sm font-bold text-ink">Ask the AI tutor</p>
            <p className="mt-0.5 text-sm text-muted">
              Confused by a step? The tutor can re-explain this lesson with a simpler example.
            </p>
          </div>
        </div>
      </Card>

      <Resources lessonId={lesson.id} />

      {/* Actions */}
      <Card className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex gap-2">
          {lesson.prev_lesson_id ? (
            <ButtonLink href={`/lessons/${lesson.prev_lesson_id}`} variant="secondary" size="sm">
              <ArrowLeft className="h-4 w-4" />
              Previous
            </ButtonLink>
          ) : (
            <Button variant="secondary" size="sm" disabled>
              <ArrowLeft className="h-4 w-4" />
              Previous
            </Button>
          )}
          {lesson.next_lesson_id ? (
            <ButtonLink href={`/lessons/${lesson.next_lesson_id}`} variant="secondary" size="sm">
              Next
              <ArrowRight className="h-4 w-4" />
            </ButtonLink>
          ) : (
            <Button variant="secondary" size="sm" disabled>
              Next
              <ArrowRight className="h-4 w-4" />
            </Button>
          )}
        </div>

        <div className="flex flex-wrap gap-2">
          {lesson.quiz_id && (
            <ButtonLink href={`/quizzes/${lesson.quiz_id}`} variant="secondary" size="sm">
              <ClipboardCheck className="h-4 w-4" />
              Take quiz
            </ButtonLink>
          )}
          {lesson.completed ? (
            <Button variant="secondary" size="sm" disabled>
              <CheckCircle2 className="h-4 w-4 text-emerald-500" />
              Completed
            </Button>
          ) : (
            <Button size="sm" loading={saving} onClick={markComplete}>
              <CheckCircle2 className="h-4 w-4" />
              Mark as complete
            </Button>
          )}
        </div>
      </Card>

      {lesson.completed && lesson.next_lesson_id && (
        <Link
          href={`/lessons/${lesson.next_lesson_id}`}
          className="flex items-center justify-between rounded-2xl bg-navy-700 p-5 text-white transition hover:bg-navy-800"
        >
          <div>
            <p className="text-xs text-white/60">Up next</p>
            <p className="font-display text-base font-bold">Continue to the next lesson</p>
          </div>
          <ArrowRight className="h-5 w-5 text-gold-300" />
        </Link>
      )}
    </div>
  );
}
