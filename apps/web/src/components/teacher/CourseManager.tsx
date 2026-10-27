"use client";

/**
 * Owner-only panel on the course page: add topics, add lessons, and manage each lesson's quiz.
 * Everything calls the existing authoring endpoints; the backend re-checks ownership.
 */
import { useState } from "react";
import { ChevronDown, ListChecks, Plus } from "lucide-react";

import QuizEditor from "@/components/teacher/QuizEditor";
import { Button, Card, CardHeader, Input } from "@/components/ui";
import { api } from "@/lib/api";
import type { CourseDetail } from "@/types";

export default function CourseManager({ course, onChanged }: { course: CourseDetail; onChanged: () => void }) {
  const [topicTitle, setTopicTitle] = useState("");
  const [lessonFor, setLessonFor] = useState<number | null>(null); // topic id with the lesson form open
  const [quizFor, setQuizFor] = useState<number | null>(null); // lesson id with the quiz editor open
  const [lesson, setLesson] = useState({ title: "", summary: "", minutes: "10", content: "" });
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function run(fn: () => Promise<unknown>) {
    setError(null);
    setBusy(true);
    try {
      await fn();
      onChanged();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong.");
    } finally {
      setBusy(false);
    }
  }

  const addTopic = (e: React.FormEvent) => {
    e.preventDefault();
    run(async () => {
      await api.post(`/courses/${course.id}/topics`, { title: topicTitle, order_index: course.topics.length + 1 });
      setTopicTitle("");
    });
  };

  const addLesson = (e: React.FormEvent, topicId: number, count: number) => {
    e.preventDefault();
    run(async () => {
      await api.post("/lessons", {
        topic_id: topicId,
        title: lesson.title,
        summary: lesson.summary,
        content: lesson.content,
        duration_minutes: Number(lesson.minutes) || 10,
        order_index: count + 1,
      });
      setLesson({ title: "", summary: "", minutes: "10", content: "" });
      setLessonFor(null);
    });
  };

  return (
    <Card className="p-5 sm:p-6">
      <CardHeader title="Manage this course" subtitle="Add topics, lessons and quizzes. Students see changes immediately." />

      {error && <p className="mt-3 rounded-xl bg-rose-50 px-4 py-2.5 text-sm font-medium text-rose-700">{error}</p>}

      <form onSubmit={addTopic} className="mt-4 flex flex-col gap-2 sm:flex-row sm:items-end">
        <div className="flex-1">
          <Input label="New topic" name="topic" required minLength={2} value={topicTitle} onChange={(e) => setTopicTitle(e.target.value)} placeholder="e.g. Forces & Motion" />
        </div>
        <Button type="submit" loading={busy}>
          <Plus className="h-4 w-4" /> Add topic
        </Button>
      </form>

      <div className="mt-5 space-y-4">
        {course.topics.map((topic) => (
          <div key={topic.id} className="rounded-2xl border border-line p-3 sm:p-4">
            <div className="flex items-center justify-between gap-2">
              <p className="font-semibold text-ink">{topic.title}</p>
              <button
                onClick={() => setLessonFor(lessonFor === topic.id ? null : topic.id)}
                className="inline-flex h-10 items-center gap-1.5 rounded-xl px-3 text-sm font-semibold text-brand-600 hover:bg-brand-50"
              >
                <Plus className="h-4 w-4" /> Lesson
              </button>
            </div>

            {topic.lessons.map((l) => (
              <div key={l.id} className="mt-2 rounded-xl bg-mist/50 px-3 py-2">
                <div className="flex items-center justify-between gap-2">
                  <p className="min-w-0 truncate text-sm font-medium text-ink">{l.title}</p>
                  <button
                    onClick={() => setQuizFor(quizFor === l.id ? null : l.id)}
                    className="inline-flex h-10 shrink-0 items-center gap-1.5 rounded-xl px-3 text-sm font-semibold text-navy-700 hover:bg-white"
                  >
                    <ListChecks className="h-4 w-4" /> Quiz
                    <ChevronDown className={`h-4 w-4 transition ${quizFor === l.id ? "rotate-180" : ""}`} />
                  </button>
                </div>
                {quizFor === l.id && <QuizEditor lessonId={l.id} onSaved={onChanged} />}
              </div>
            ))}

            {lessonFor === topic.id && (
              <form onSubmit={(e) => addLesson(e, topic.id, topic.lessons.length)} className="mt-3 space-y-3 rounded-2xl bg-brand-50/60 p-3 sm:p-4">
                <Input label="Lesson title" name="ltitle" required minLength={2} value={lesson.title} onChange={(e) => setLesson({ ...lesson, title: e.target.value })} />
                <div className="grid grid-cols-[1fr_110px] gap-3">
                  <Input label="Short summary" name="lsummary" value={lesson.summary} onChange={(e) => setLesson({ ...lesson, summary: e.target.value })} />
                  <Input label="Minutes" name="lmin" type="number" min={1} max={240} value={lesson.minutes} onChange={(e) => setLesson({ ...lesson, minutes: e.target.value })} />
                </div>
                <div>
                  <label className="label" htmlFor={`content-${topic.id}`}>Lesson content</label>
                  <textarea id={`content-${topic.id}`} rows={7} className="input-base" value={lesson.content} onChange={(e) => setLesson({ ...lesson, content: e.target.value })} placeholder="Write the lesson. The AI tutor and quiz generator use this text. Use **bold** and blank lines between paragraphs." />
                </div>
                <div className="flex flex-col-reverse gap-2 sm:flex-row sm:justify-end">
                  <Button type="button" variant="secondary" onClick={() => setLessonFor(null)}>Cancel</Button>
                  <Button type="submit" loading={busy}>Save lesson</Button>
                </div>
              </form>
            )}
          </div>
        ))}
        {course.topics.length === 0 && <p className="text-sm text-muted">No topics yet — add your first topic above.</p>}
      </div>
    </Card>
  );
}
