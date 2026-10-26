"use client";

/**
 * Quiz page.
 *
 * One question at a time, then submit all answers to the backend for grading
 * (correct answers are never sent to the client before submission). The result
 * screen shows per-question feedback and a retry option.
 */
import { useParams, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import {
  ArrowLeft,
  ArrowRight,
  CheckCircle2,
  ClipboardCheck,
  RotateCcw,
  Sparkles,
  XCircle,
} from "lucide-react";

import { Badge, Button, ButtonLink, Card, EmptyState, ProgressBar, Skeleton } from "@/components/ui";
import { api } from "@/lib/api";
import { cn } from "@/lib/utils";
import type { AttemptResult, Quiz } from "@/types";

export default function QuizPage() {
  const params = useParams<{ id: string }>();
  const router = useRouter();

  const [quiz, setQuiz] = useState<Quiz | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [index, setIndex] = useState(0);
  const [answers, setAnswers] = useState<Record<number, number>>({});
  const [submitting, setSubmitting] = useState(false);
  const [result, setResult] = useState<AttemptResult | null>(null);

  useEffect(() => {
    api
      .get<Quiz>(`/quizzes/${params.id}`)
      .then(setQuiz)
      .catch((err) => setError(err instanceof Error ? err.message : "Could not load this quiz."));
  }, [params.id]);

  async function submit() {
    if (!quiz) return;
    setSubmitting(true);
    try {
      const payload = quiz.questions.map((_, i) => answers[i] ?? -1);
      const data = await api.post<AttemptResult>(`/quizzes/${quiz.id}/attempts`, { answers: payload });
      setResult(data);
      window.scrollTo({ top: 0, behavior: "smooth" });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not submit your answers.");
    } finally {
      setSubmitting(false);
    }
  }

  function retry() {
    setResult(null);
    setAnswers({});
    setIndex(0);
  }

  if (error) {
    return (
      <EmptyState
        icon={<ClipboardCheck className="h-5 w-5" />}
        title="Quiz unavailable"
        description={error}
        action={<ButtonLink href="/courses">Back to courses</ButtonLink>}
      />
    );
  }

  if (!quiz) {
    return (
      <div className="mx-auto max-w-2xl space-y-6">
        <Skeleton className="h-10 w-40" />
        <Skeleton className="h-80 w-full" />
      </div>
    );
  }

  /* ------------------------------------------------------------- Results */
  if (result) {
    const passed = result.score >= 70;
    return (
      <div className="mx-auto max-w-2xl space-y-6">
        <Card className="text-center">
          <span
            className={cn(
              "mx-auto flex h-16 w-16 items-center justify-center rounded-3xl",
              passed ? "bg-emerald-50 text-emerald-600" : "bg-amber-50 text-amber-600"
            )}
          >
            {passed ? <CheckCircle2 className="h-8 w-8" /> : <Sparkles className="h-8 w-8" />}
          </span>
          <h1 className="mt-4 font-display text-2xl font-extrabold text-ink">
            {passed ? "Nice work!" : "Good effort — keep going"}
          </h1>
          <p className="mt-1 text-sm text-muted">
            You scored {result.correct_count} out of {result.total}.
          </p>
          <p className="mt-4 font-display text-5xl font-extrabold text-brand-600">{Math.round(result.score)}%</p>
          <div className="mt-6 flex flex-wrap justify-center gap-3">
            <Button variant="secondary" onClick={retry}>
              <RotateCcw className="h-4 w-4" />
              Try again
            </Button>
            <ButtonLink href="/dashboard">Back to dashboard</ButtonLink>
          </div>
        </Card>

        <div className="space-y-3">
          {result.results.map((item, i) => (
            <Card key={i} className={cn("p-5", item.is_correct ? "border-emerald-200" : "border-rose-200")}>
              <div className="flex items-start gap-3">
                <span
                  className={cn(
                    "mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-full",
                    item.is_correct ? "bg-emerald-50 text-emerald-600" : "bg-rose-50 text-rose-600"
                  )}
                >
                  {item.is_correct ? <CheckCircle2 className="h-4 w-4" /> : <XCircle className="h-4 w-4" />}
                </span>
                <div className="min-w-0 flex-1">
                  <p className="font-semibold text-ink">{item.prompt}</p>
                  <p className="mt-1 text-sm text-muted">{item.explanation}</p>
                  {!item.is_correct && item.selected !== null && item.selected >= 0 && (
                    <p className="mt-2 text-xs text-rose-600">
                      Your answer was incorrect. Review the explanation above and try again.
                    </p>
                  )}
                </div>
              </div>
            </Card>
          ))}
        </div>
      </div>
    );
  }

  /* ------------------------------------------------------ Question flow */
  const question = quiz.questions[index];
  const selected = answers[index];
  const isLast = index === quiz.questions.length - 1;
  const answeredCount = Object.keys(answers).length;

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <button
        onClick={() => router.back()}
        className="inline-flex items-center gap-2 text-sm font-semibold text-muted hover:text-ink"
      >
        <ArrowLeft className="h-4 w-4" />
        Back to lesson
      </button>

      <div>
        <div className="flex items-center justify-between">
          <Badge tone="blue">Checkpoint quiz</Badge>
          <span className="text-xs font-semibold text-muted">
            Question {index + 1} of {quiz.questions.length}
          </span>
        </div>
        <h1 className="mt-3 font-display text-2xl font-extrabold tracking-tight text-ink">{quiz.title}</h1>
        <ProgressBar
          value={((index + 1) / quiz.questions.length) * 100}
          size="sm"
          className="mt-4"
        />
      </div>

      <Card className="p-6 sm:p-8">
        <p className="font-display text-lg font-bold text-ink">{question.prompt}</p>
        <div className="mt-5 space-y-3">
          {question.options.map((option, optionIndex) => {
            const active = selected === optionIndex;
            return (
              <button
                key={optionIndex}
                onClick={() => setAnswers((prev) => ({ ...prev, [index]: optionIndex }))}
                className={cn(
                  "flex w-full items-center gap-3 rounded-2xl border p-4 text-left text-sm font-medium transition",
                  active
                    ? "border-brand-500 bg-brand-50/70 text-ink ring-4 ring-brand-500/10"
                    : "border-line bg-white text-ink hover:border-brand-300 hover:bg-mist/40"
                )}
              >
                <span
                  className={cn(
                    "flex h-8 w-8 shrink-0 items-center justify-center rounded-full text-xs font-bold",
                    active ? "bg-brand-500 text-white" : "bg-mist text-muted"
                  )}
                >
                  {String.fromCharCode(65 + optionIndex)}
                </span>
                {option}
              </button>
            );
          })}
        </div>
      </Card>

      <div className="flex items-center justify-between gap-3">
        <Button
          variant="secondary"
          onClick={() => setIndex((i) => Math.max(0, i - 1))}
          disabled={index === 0}
        >
          <ArrowLeft className="h-4 w-4" />
          Previous
        </Button>

        {isLast ? (
          <Button onClick={submit} loading={submitting} disabled={answeredCount < quiz.questions.length}>
            <ClipboardCheck className="h-4 w-4" />
            Submit answers
          </Button>
        ) : (
          <Button onClick={() => setIndex((i) => Math.min(quiz.questions.length - 1, i + 1))} disabled={selected === undefined}>
            Next question
            <ArrowRight className="h-4 w-4" />
          </Button>
        )}
      </div>

      {answeredCount < quiz.questions.length && isLast && (
        <p className="text-center text-xs text-muted">
          Answer all {quiz.questions.length} questions to submit ({answeredCount} done).
        </p>
      )}
    </div>
  );
}
