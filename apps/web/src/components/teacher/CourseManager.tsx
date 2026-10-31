"use client";

/**
 * Owner-only panel on the course page: add topics, add lessons, and manage each lesson's quiz.
 * Everything calls the existing authoring endpoints; the backend re-checks ownership.
 */
import { useEffect, useRef, useState } from "react";
import { ChevronDown, Copy, FileUp, Link2, ListChecks, Plus, RefreshCw, Sparkles, Trash2 } from "lucide-react";

import QuizEditor from "@/components/teacher/QuizEditor";
import { Button, Card, CardHeader, Input } from "@/components/ui";
import { api, apiUpload } from "@/lib/api";
import type { CourseDetail } from "@/types";


/** Class code teachers share so students can join (PDF FR-06). */
function JoinCodeCard({ courseId }: { courseId: number }) {
  const [code, setCode] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);
  useEffect(() => {
    api.get<{ code: string }>(`/courses/${courseId}/join-code`).then((d) => setCode(d.code)).catch(() => undefined);
  }, [courseId]);

  async function reset() {
    if (!confirm("Generate a new code? The old code will stop working.")) return;
    const d = await api.post<{ code: string }>(`/courses/${courseId}/join-code/reset`);
    setCode(d.code);
  }
  async function copy() {
    if (!code) return;
    try {
      await navigator.clipboard.writeText(code);
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    } catch {
      /* clipboard blocked */
    }
  }
  return (
    <div className="rounded-2xl bg-brand-50 p-4">
      <p className="text-xs font-bold uppercase tracking-wider text-brand-600">Class code</p>
      <div className="mt-1 flex flex-wrap items-center gap-2">
        <span className="font-display text-3xl font-extrabold tracking-[0.2em] text-ink">{code ?? "······"}</span>
        <button onClick={copy} className="inline-flex h-10 items-center gap-1.5 rounded-xl border border-line bg-white px-3 text-sm font-semibold text-ink">
          <Copy className="h-4 w-4" /> {copied ? "Copied" : "Copy"}
        </button>
        <button onClick={reset} className="inline-flex h-10 items-center gap-1.5 rounded-xl px-3 text-sm font-semibold text-muted hover:bg-white" aria-label="Generate a new code">
          <RefreshCw className="h-4 w-4" /> New
        </button>
      </div>
      <p className="mt-1 text-xs text-muted">Students enter this on the Courses page (&ldquo;Join with a class code&rdquo;).</p>
    </div>
  );
}

/** Upload a PDF -> its text is added to the lesson box for you to review (the PDF is not stored). */
function PdfImport({ onText }: { onText: (t: string) => void }) {
  const input = useRef<HTMLInputElement>(null);
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState<string | null>(null);
  async function pick(e: React.ChangeEvent<HTMLInputElement>) {
    const f = e.target.files?.[0];
    e.target.value = "";
    if (!f) return;
    setBusy(true); setMsg(null);
    try {
      const d = await apiUpload<{ text: string; pages: number }>("/materials/extract-pdf", f);
      onText(d.text);
      setMsg(`Imported ${d.pages} page(s). Review and edit the text below.`);
    } catch (x) {
      setMsg(x instanceof Error ? x.message : "Could not import that PDF.");
    } finally { setBusy(false); }
  }
  return (
    <div>
      <input ref={input} type="file" accept="application/pdf" className="hidden" onChange={pick} />
      <Button type="button" variant="secondary" loading={busy} onClick={() => input.current?.click()}>
        <FileUp className="h-4 w-4" /> Import text from a PDF
      </Button>
      {msg && <p className="mt-1.5 text-xs text-muted">{msg}</p>}
    </div>
  );
}

/** Extra reading links for one lesson. */
function ResourceLinks({ lessonId }: { lessonId: number }) {
  const [items, setItems] = useState<{ id: number; title: string; url: string }[]>([]);
  const [title, setTitle] = useState("");
  const [url, setUrl] = useState("");
  const [err, setErr] = useState<string | null>(null);
  const load = () => api.get<typeof items>(`/lessons/${lessonId}/resources`).then(setItems).catch(() => undefined);
  useEffect(() => { load(); /* eslint-disable-next-line react-hooks/exhaustive-deps */ }, [lessonId]);

  async function add(e: React.FormEvent) {
    e.preventDefault();
    setErr(null);
    try {
      await api.post(`/lessons/${lessonId}/resources`, { title, url });
      setTitle(""); setUrl(""); load();
    } catch (x) {
      setErr(x instanceof Error ? x.message : "Could not add the link (it must start with https://).");
    }
  }
  return (
    <div className="mt-3 rounded-2xl bg-mist/70 p-3 sm:p-4">
      <p className="flex items-center gap-1.5 text-sm font-semibold text-ink"><Link2 className="h-4 w-4" /> Resource links</p>
      {items.map((r) => (
        <div key={r.id} className="mt-2 flex items-center justify-between gap-2 text-sm">
          <a href={r.url} target="_blank" rel="noopener noreferrer" className="min-w-0 truncate text-brand-600">{r.title}</a>
          <button onClick={async () => { await api.delete(`/resources/${r.id}`); load(); }} className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg text-rose-500 hover:bg-white" aria-label={`Remove ${r.title}`}>
            <Trash2 className="h-4 w-4" />
          </button>
        </div>
      ))}
      <form onSubmit={add} className="mt-3 grid gap-2 sm:grid-cols-[1fr_1.4fr_auto]">
        <input className="input-base !py-2" placeholder="Title" value={title} onChange={(e) => setTitle(e.target.value)} required minLength={2} aria-label="Resource title" />
        <input className="input-base !py-2" placeholder="YouTube, Instagram, Zoom/Meet recording or any link" type="url" value={url} onChange={(e) => setUrl(e.target.value)} required aria-label="Resource URL" />
        <Button type="submit" variant="secondary">Add</Button>
      </form>
      {err && <p className="mt-2 text-xs font-medium text-rose-600">{err}</p>}
    </div>
  );
}

export default function CourseManager({ course, onChanged }: { course: CourseDetail; onChanged: () => void }) {
  const [topicTitle, setTopicTitle] = useState("");
  const [lessonFor, setLessonFor] = useState<number | null>(null); // topic id with the lesson form open
  const [quizFor, setQuizFor] = useState<number | null>(null); // lesson id with the quiz editor open
  const [lesson, setLesson] = useState({ title: "", summary: "", minutes: "10", content: "" });
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [ideas, setIdeas] = useState<string[]>([]);
  const [ai, setAi] = useState<"topics" | "draft" | null>(null);
  const [aiNote, setAiNote] = useState<string | null>(null);

  async function suggestTopics() {
    setAi("topics");
    setAiNote(null);
    try {
      const r = await api.post<{ topics: string[]; provider: string }>("/ai/suggest-topics", {
        course_title: course.title,
        description: course.description ?? "",
      });
      const have = new Set(course.topics.map((t) => t.title.toLowerCase()));
      setIdeas(r.topics.filter((t) => !have.has(t.toLowerCase())));
      if (r.provider !== "gemini") setAiNote("AI is offline, so these are generic starting points. Edit them to fit your course.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not suggest topics.");
    } finally {
      setAi(null);
    }
  }

  async function draftLesson() {
    if (lesson.title.trim().length < 3) {
      setError("Type a lesson title first, then I can draft it for you.");
      return;
    }
    setError(null);
    setAi("draft");
    setAiNote(null);
    try {
      const r = await api.post<{ summary: string; content: string; provider: string }>("/ai/draft-lesson", {
        title: lesson.title,
        course_title: course.title,
        level: course.level ?? "Beginner",
      });
      setLesson((l) => ({ ...l, summary: l.summary || r.summary, content: l.content ? l.content + "\n\n" + r.content : r.content }));
      setAiNote(
        r.provider === "gemini"
          ? "Draft added. Read it carefully, fix anything inaccurate, and add your own examples before saving."
          : "AI is offline, so I added a template. Fill in each section."
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not draft the lesson.");
    } finally {
      setAi(null);
    }
  }

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

      <div className="mt-4"><JoinCodeCard courseId={course.id} /></div>

      {error && <p className="mt-3 rounded-xl bg-rose-50 px-4 py-2.5 text-sm font-medium text-rose-700">{error}</p>}

      <form onSubmit={addTopic} className="mt-4 flex flex-col gap-2 sm:flex-row sm:items-end">
        <div className="flex-1">
          <Input label="New topic" name="topic" required minLength={2} value={topicTitle} onChange={(e) => setTopicTitle(e.target.value)} placeholder="e.g. Forces & Motion" />
        </div>
        <Button type="submit" loading={busy}>
          <Plus className="h-4 w-4" /> Add topic
        </Button>
        <Button type="button" variant="secondary" loading={ai === "topics"} onClick={suggestTopics}>
          <Sparkles className="h-4 w-4" /> Suggest topics
        </Button>
      </form>
      {ideas.length > 0 && (
        <div className="mt-3 rounded-2xl bg-brand-50/60 p-3">
          <p className="text-xs font-semibold text-brand-700">Tap a topic to add it to your course</p>
          <div className="mt-2 flex flex-wrap gap-2">
            {ideas.map((t) => (
              <button
                key={t}
                type="button"
                disabled={busy}
                onClick={() => {
                  setIdeas((xs) => xs.filter((x) => x !== t));
                  run(async () => {
                    await api.post(`/courses/${course.id}/topics`, { title: t, order_index: course.topics.length + 1 });
                  });
                }}
                className="min-h-[40px] rounded-full border border-brand-200 bg-white px-3.5 text-sm font-medium text-brand-700 hover:bg-brand-50 disabled:opacity-60"
              >
                <Plus className="mr-1 inline h-3.5 w-3.5" />
                {t}
              </button>
            ))}
          </div>
        </div>
      )}
      {aiNote && ai === null && ideas.length > 0 && <p className="mt-2 text-xs text-amber-700">{aiNote}</p>}

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
                    <ListChecks className="h-4 w-4" /> Quiz &amp; links
                    <ChevronDown className={`h-4 w-4 transition ${quizFor === l.id ? "rotate-180" : ""}`} />
                  </button>
                </div>
                {quizFor === l.id && (
                  <>
                    <QuizEditor lessonId={l.id} onSaved={onChanged} />
                    <ResourceLinks lessonId={l.id} />
                  </>
                )}
              </div>
            ))}

            {lessonFor === topic.id && (
              <form onSubmit={(e) => addLesson(e, topic.id, topic.lessons.length)} className="mt-3 space-y-3 rounded-2xl bg-brand-50/60 p-3 sm:p-4">
                <Input label="Lesson title" name="ltitle" required minLength={2} value={lesson.title} onChange={(e) => setLesson({ ...lesson, title: e.target.value })} />
                <div className="grid grid-cols-[1fr_110px] gap-3">
                  <Input label="Short summary" name="lsummary" value={lesson.summary} onChange={(e) => setLesson({ ...lesson, summary: e.target.value })} />
                  <Input label="Minutes" name="lmin" type="number" min={1} max={240} value={lesson.minutes} onChange={(e) => setLesson({ ...lesson, minutes: e.target.value })} />
                </div>
                <div className="flex flex-wrap gap-2">
                  <Button type="button" variant="secondary" loading={ai === "draft"} onClick={draftLesson}>
                    <Sparkles className="h-4 w-4" /> Draft with AI
                  </Button>
                </div>
                {aiNote && <p className="rounded-xl bg-amber-50 px-3 py-2 text-xs font-medium text-amber-800">{aiNote}</p>}
                <PdfImport onText={(t) => setLesson((l) => ({ ...l, content: l.content ? l.content + "\n\n" + t : t }))} />
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
        {course.topics.length === 0 && <p className="rounded-2xl bg-mist/70 p-4 text-sm text-muted">
            No topics yet. A topic is a chapter, like &ldquo;Forces &amp; Motion&rdquo;. Type one above, or tap <strong>Suggest topics</strong> and I&apos;ll propose an outline.
            Then add lessons to each topic (type, paste, or import a PDF), and attach videos under <strong>Quiz &amp; links</strong>.
          </p>}
      </div>
    </Card>
  );
}
