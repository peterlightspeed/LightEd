"use client";

/**
 * Live classes for ONE course.
 * Teacher: schedule a class by pasting a Google Meet / Zoom / Teams link. Enrolled students are notified.
 * Student: see upcoming classes and tap Join (opens the meeting link). "Live now" opens 10 min early.
 */
import { useCallback, useEffect, useState } from "react";
import { CalendarClock, ExternalLink, Trash2, Video } from "lucide-react";

import { Badge, Button, Card, Input, Select } from "@/components/ui";
import { api } from "@/lib/api";
import type { LiveSessionItem } from "@/types";

export const fmtWhen = (iso: string) =>
  new Date(iso).toLocaleString(undefined, { weekday: "short", month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" });

export function SessionRow({ s, onDelete }: { s: LiveSessionItem; onDelete?: () => void }) {
  return (
    <div className="flex flex-col gap-3 py-3 sm:flex-row sm:items-center">
      <div className="flex min-w-0 flex-1 items-start gap-3">
        <span className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-xl ${s.status === "live" ? "bg-emerald-50 text-emerald-600" : "bg-brand-50 text-brand-600"}`}>
          <Video className="h-5 w-5" />
        </span>
        <div className="min-w-0">
          <p className="truncate font-semibold text-ink">{s.title}</p>
          <p className="text-xs text-muted">
            {s.course_title ? `${s.course_title} · ` : ""}
            {fmtWhen(s.starts_at)} · {s.duration_minutes} min
          </p>
        </div>
      </div>
      <div className="flex items-center gap-2">
        {s.status === "live" ? <Badge tone="green">Live now</Badge> : s.status === "ended" ? <Badge tone="neutral">Ended</Badge> : <Badge tone="blue">Upcoming</Badge>}
        {s.status !== "ended" && (
          <a
            href={s.link}
            target="_blank"
            rel="noopener noreferrer"
            className={`inline-flex min-h-[44px] items-center gap-1.5 rounded-xl px-4 text-sm font-semibold ${s.status === "live" ? "bg-emerald-600 text-white hover:bg-emerald-700" : "border border-line text-ink hover:bg-mist"}`}
          >
            Join <ExternalLink className="h-4 w-4" />
          </a>
        )}
        {onDelete && (
          <button onClick={onDelete} aria-label={`Delete ${s.title}`} className="flex h-11 w-11 items-center justify-center rounded-xl text-rose-500 hover:bg-rose-50">
            <Trash2 className="h-4 w-4" />
          </button>
        )}
      </div>
    </div>
  );
}

export default function SessionsPanel({ courseId, canManage }: { courseId: number; canManage: boolean }) {
  const [items, setItems] = useState<LiveSessionItem[] | null>(null);
  const [title, setTitle] = useState("");
  const [when, setWhen] = useState("");
  const [minutes, setMinutes] = useState("60");
  const [link, setLink] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(() => {
    api.get<LiveSessionItem[]>(`/courses/${courseId}/sessions`).then(setItems).catch(() => setItems([]));
  }, [courseId]);
  useEffect(load, [load]);

  async function schedule(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setBusy(true);
    try {
      await api.post(`/courses/${courseId}/sessions`, {
        title,
        starts_at: new Date(when).toISOString(), // datetime-local is the teacher's local time -> convert to UTC
        duration_minutes: Number(minutes),
        link,
      });
      setTitle(""); setWhen(""); setLink("");
      load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not schedule the class.");
    } finally {
      setBusy(false);
    }
  }

  if (!canManage && items !== null && items.length === 0) {
    return (
      <Card className="p-5">
        <p className="flex items-center gap-2 font-display font-bold text-ink"><CalendarClock className="h-4 w-4 text-brand-600" /> Live classes</p>
        <p className="mt-1 text-sm text-muted">No live classes scheduled yet. You&apos;ll get a notification when your teacher schedules one.</p>
      </Card>
    );
  }

  return (
    <Card className="p-5 sm:p-6">
      <p className="flex items-center gap-2 font-display text-lg font-bold text-ink"><CalendarClock className="h-5 w-5 text-brand-600" /> Live classes</p>
      <p className="text-sm text-muted">{canManage ? "Schedule a class with a Meet, Zoom or Teams link. Students are notified." : "Join your teacher's live sessions."}</p>

      <div className="mt-3 divide-y divide-line/70">
        {items === null && <p className="py-3 text-sm text-muted">Loading…</p>}
        {items?.length === 0 && <p className="py-3 text-sm text-muted">Nothing scheduled yet.</p>}
        {items?.map((s) => (
          <SessionRow key={s.id} s={s} onDelete={canManage ? async () => { await api.delete(`/sessions/${s.id}`); load(); } : undefined} />
        ))}
      </div>

      {canManage && (
        <form onSubmit={schedule} className="mt-4 space-y-3 rounded-2xl bg-mist/70 p-3 sm:p-4">
          <p className="text-sm font-semibold text-ink">Schedule a class</p>
          <Input label="Title" name="stitle" required minLength={3} value={title} onChange={(e) => setTitle(e.target.value)} placeholder="e.g. Week 1: Atoms and molecules" />
          <div className="grid gap-3 sm:grid-cols-2">
            <Input label="Date and time" name="swhen" type="datetime-local" required value={when} onChange={(e) => setWhen(e.target.value)} />
            <Select label="Length" value={minutes} onChange={(e) => setMinutes(e.target.value)}>
              {[30, 45, 60, 90, 120].map((m) => <option key={m} value={m}>{m} minutes</option>)}
            </Select>
          </div>
          <Input label="Meeting link" name="slink" type="url" required value={link} onChange={(e) => setLink(e.target.value)} placeholder="https://meet.google.com/..." />
          <p className="text-xs text-muted">
            No link yet? Open <a className="font-semibold text-brand-600" href="https://meet.google.com/new" target="_blank" rel="noopener noreferrer">meet.google.com/new</a>, copy the link and paste it here.
          </p>
          {error && <p className="rounded-xl bg-rose-50 px-3 py-2 text-sm font-medium text-rose-700">{error}</p>}
          <Button type="submit" loading={busy}>Schedule class</Button>
        </form>
      )}
    </Card>
  );
}
