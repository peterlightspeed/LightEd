"use client";

/** Teacher/admin: create a course, then jump to its page to add topics + lessons. */
import { useRouter } from "next/navigation";
import { useState } from "react";

import { Button, Card, Input, Select } from "@/components/ui";
import { api } from "@/lib/api";
import type { Course } from "@/types";

const ACCENTS = ["blue", "emerald", "amber", "rose", "violet"];

export default function NewCourseForm({ onCancel, initial }: { onCancel: () => void; initial?: { title?: string; subject?: string; level?: string; description?: string } }) {
  const router = useRouter();
  const [title, setTitle] = useState(initial?.title ?? "");
  const [subject, setSubject] = useState(initial?.subject ?? "General");
  const [level, setLevel] = useState(initial?.level ?? "Beginner");
  const [accent, setAccent] = useState("blue");
  const [description, setDescription] = useState(initial?.description ?? "");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setBusy(true);
    try {
      const course = await api.post<Course>("/courses", { title, subject, level, accent, description });
      router.push(`/courses/${course.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not create the course.");
      setBusy(false);
    }
  }

  return (
    <Card className="p-5 sm:p-6">
      <h2 className="font-display text-lg font-bold text-ink">Create a new course</h2>
      <p className="mt-0.5 text-sm text-muted">Next you&apos;ll add topics, lessons and quizzes.</p>
      <form onSubmit={submit} className="mt-4 space-y-4">
        <Input label="Course title" name="title" required minLength={3} value={title} onChange={(e) => setTitle(e.target.value)} placeholder="e.g. Intro to Chemistry" />
        <div className="grid gap-4 sm:grid-cols-3">
          <Input label="Subject" name="subject" value={subject} onChange={(e) => setSubject(e.target.value)} />
          <Select label="Level" value={level} onChange={(e) => setLevel(e.target.value)}>
            <option>Beginner</option>
            <option>Intermediate</option>
            <option>Advanced</option>
          </Select>
          <Select label="Colour" value={accent} onChange={(e) => setAccent(e.target.value)}>
            {ACCENTS.map((a) => (
              <option key={a} value={a}>
                {a[0].toUpperCase() + a.slice(1)}
              </option>
            ))}
          </Select>
        </div>
        <div>
          <label className="label" htmlFor="desc">Description</label>
          <textarea id="desc" rows={3} className="input-base" value={description} onChange={(e) => setDescription(e.target.value)} placeholder="What will students learn?" />
        </div>
        {error && <p className="rounded-xl bg-rose-50 px-4 py-2.5 text-sm font-medium text-rose-700">{error}</p>}
        <div className="flex flex-col-reverse gap-2 sm:flex-row sm:justify-end">
          <Button type="button" variant="secondary" onClick={onCancel}>Cancel</Button>
          <Button type="submit" loading={busy}>Create course</Button>
        </div>
      </form>
    </Card>
  );
}
