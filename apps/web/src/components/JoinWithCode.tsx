"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { Button, Card } from "@/components/ui";
import { api } from "@/lib/api";

/** Student: enter a teacher's class code to join their course (PDF FR-06). */
export default function JoinWithCode() {
  const router = useRouter();
  const [code, setCode] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function join(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setBusy(true);
    try {
      const d = await api.post<{ course_id: number }>("/courses/join", { code });
      router.push(`/courses/${d.course_id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not join with that code.");
      setBusy(false);
    }
  }

  return (
    <Card className="p-4 sm:p-5">
      <form onSubmit={join} className="flex flex-col gap-3 sm:flex-row sm:items-center">
        <div className="min-w-0 flex-1">
          <p className="font-display font-bold text-ink">Join with a class code</p>
          <p className="text-xs text-muted">Your teacher gave you a 6-character code.</p>
        </div>
        <input
          value={code}
          onChange={(e) => setCode(e.target.value.toUpperCase())}
          maxLength={8}
          placeholder="ABC123"
          aria-label="Class code"
          className="input-base text-center font-mono tracking-[0.25em] sm:w-40"
        />
        <Button type="submit" loading={busy} disabled={code.trim().length < 4}>Join</Button>
      </form>
      {error && <p className="mt-2 text-sm font-medium text-rose-600">{error}</p>}
    </Card>
  );
}
