"use client";

/**
 * Quiz authoring for ONE lesson:
 *   1) "Generate draft" asks the backend (Gemini if configured, else offline fallback),
 *   2) the teacher edits every question / option / correct answer,
 *   3) "Publish quiz" saves it (then shows a "Published" badge; "Save changes" appears only after edits) (PUT /lessons/{id}/quiz). Students only ever see published quizzes.
 */
import { useEffect, useState } from "react";
import { CheckCircle2, Plus, Sparkles, Trash2 } from "lucide-react";

import { Button, Select } from "@/components/ui";
import { api } from "@/lib/api";
import type { DraftQuestion } from "@/types";

const blank = (): DraftQuestion => ({ prompt: "", options: ["", "", "", ""], answer_index: 0, explanation: "" });

export default function QuizEditor({ lessonId, onSaved }: { lessonId: number; onSaved: () => void }) {
  const [questions, setQuestions] = useState<DraftQuestion[]>([]);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState<"gen" | "save" | null>(null);
  const [n, setN] = useState("5");
  const [difficulty, setDifficulty] = useState("medium");
  const [note, setNote] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  // JSON of the last published version (null = never published). Drives the publish button below.
  const [saved, setSaved] = useState<string | null>(null);
  const published = saved !== null;
  const dirty = published && JSON.stringify(questions) !== saved;

  // Load the existing quiz (with answers) if there is one.
  useEffect(() => {
    api
      .get<{ questions: DraftQuestion[] }>(`/lessons/${lessonId}/quiz/edit`)
      .then((d) => {
        setQuestions(d.questions);
        if (d.questions.length > 0) setSaved(JSON.stringify(d.questions));
      })
      .catch(() => undefined)
      .finally(() => setLoading(false));
  }, [lessonId]);

  const update = (i: number, patch: Partial<DraftQuestion>) =>
    setQuestions((qs) => qs.map((q, idx) => (idx === i ? { ...q, ...patch } : q)));

  async function generate() {
    setError(null);
    setNote(null);
    setBusy("gen");
    try {
      const d = await api.post<{ provider: string; questions: DraftQuestion[] }>(`/lessons/${lessonId}/quiz/generate`, {
        num_questions: Number(n),
        difficulty,
      });
      setQuestions(d.questions);
      setNote(
        d.provider === "gemini"
          ? "Drafted by AI from your lesson text. Review every question, then press Publish."
          : "Drafted from your lesson text (offline mode — no AI key set). Review and edit before publishing."
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not generate a draft.");
    } finally {
      setBusy(null);
    }
  }

  async function save() {
    setError(null);
    setBusy("save");
    try {
      await api.put(`/lessons/${lessonId}/quiz`, { questions });
      setSaved(JSON.stringify(questions));
      setNote(null);
      onSaved();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not save the quiz.");
    } finally {
      setBusy(null);
    }
  }

  if (loading) return <p className="py-3 text-sm text-muted">Loading quiz…</p>;

  return (
    <div className="mt-3 space-y-4 rounded-2xl bg-mist/70 p-3 sm:p-4">
      <div className="flex flex-col gap-2 sm:flex-row sm:items-end">
        <div className="grid grid-cols-2 gap-2 sm:w-72">
          <Select label="Questions" value={n} onChange={(e) => setN(e.target.value)}>
            {[3, 5, 8, 10].map((v) => (
              <option key={v}>{v}</option>
            ))}
          </Select>
          <Select label="Difficulty" value={difficulty} onChange={(e) => setDifficulty(e.target.value)}>
            <option>easy</option>
            <option>medium</option>
            <option>hard</option>
          </Select>
        </div>
        <Button variant="secondary" loading={busy === "gen"} onClick={generate}>
          <Sparkles className="h-4 w-4" /> Generate draft
        </Button>
      </div>

      {questions.length === 0 && <p className="text-sm text-muted">No questions yet. Generate a draft or add one manually.</p>}

      {questions.map((q, i) => (
        <div key={i} className="rounded-2xl border border-line bg-white p-3 sm:p-4">
          <div className="flex items-start gap-2">
            <span className="mt-2 text-xs font-bold text-muted">Q{i + 1}</span>
            <textarea
              rows={2}
              className="input-base"
              value={q.prompt}
              onChange={(e) => update(i, { prompt: e.target.value })}
              placeholder="Question"
              aria-label={`Question ${i + 1}`}
            />
            <button
              onClick={() => setQuestions((qs) => qs.filter((_, idx) => idx !== i))}
              className="mt-1 flex h-10 w-10 shrink-0 items-center justify-center rounded-xl text-rose-500 hover:bg-rose-50"
              aria-label={`Delete question ${i + 1}`}
            >
              <Trash2 className="h-4 w-4" />
            </button>
          </div>
          <div className="mt-3 space-y-2">
            {q.options.map((opt, oi) => (
              <label key={oi} className="flex items-center gap-2">
                <input
                  type="radio"
                  name={`correct-${lessonId}-${i}`}
                  checked={q.answer_index === oi}
                  onChange={() => update(i, { answer_index: oi })}
                  className="h-5 w-5 shrink-0 accent-emerald-600"
                  aria-label={`Mark option ${oi + 1} correct`}
                />
                <input
                  className="input-base !py-2"
                  value={opt}
                  onChange={(e) => update(i, { options: q.options.map((o, k) => (k === oi ? e.target.value : o)) })}
                  placeholder={`Option ${oi + 1}`}
                />
              </label>
            ))}
            <p className="text-[11px] text-muted">Select the circle next to the correct answer.</p>
          </div>
        </div>
      ))}

      {note && <p className="rounded-xl bg-brand-50 px-3 py-2 text-sm font-medium text-brand-700">{note}</p>}
      {error && <p className="rounded-xl bg-rose-50 px-3 py-2 text-sm font-medium text-rose-700">{error}</p>}

      <div className="flex flex-col gap-2 sm:flex-row sm:justify-between">
        <Button variant="secondary" onClick={() => setQuestions((qs) => [...qs, blank()])}>
          <Plus className="h-4 w-4" /> Add question
        </Button>
        {published && !dirty ? (
          <p className="inline-flex min-h-[44px] items-center justify-center gap-2 rounded-2xl bg-emerald-50 px-4 text-sm font-semibold text-emerald-700" role="status">
            <CheckCircle2 className="h-4 w-4" /> Published. Students can take this quiz.
          </p>
        ) : (
          <Button onClick={save} loading={busy === "save"} disabled={questions.length === 0}>
            {published ? "Save changes" : "Publish quiz"}
          </Button>
        )}
      </div>
    </div>
  );
}
