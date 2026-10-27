"use client";

/** AI tutor chat. Answers come ONLY from the user's course material and always cite sources. */
import { useEffect, useRef, useState } from "react";
import { Send, Sparkles } from "lucide-react";

import { api } from "@/lib/api";

interface Msg { role: "user" | "tutor"; text: string; sources?: string[] }

const SUGGESTIONS = ["Explain this in simple words", "Give me an example", "What should I focus on first?"];

export default function TutorPage() {
  const [msgs, setMsgs] = useState<Msg[]>([
    { role: "tutor", text: "Hi! Ask me anything about your enrolled courses. I answer from your lesson material and show my sources." },
  ]);
  const [text, setText] = useState("");
  const [busy, setBusy] = useState(false);
  const end = useRef<HTMLDivElement>(null);
  useEffect(() => end.current?.scrollIntoView({ behavior: "smooth", block: "end" }), [msgs, busy]);

  async function ask(q: string) {
    if (!q.trim() || busy) return;
    setMsgs((m) => [...m, { role: "user", text: q }]);
    setText("");
    setBusy(true);
    try {
      const r = await api.post<{ answer: string; sources: string[] }>("/ai/tutor", { question: q });
      setMsgs((m) => [...m, { role: "tutor", text: r.answer, sources: r.sources }]);
    } catch (err) {
      setMsgs((m) => [...m, { role: "tutor", text: err instanceof Error ? err.message : "Sorry, I couldn't answer that." }]);
    } finally {
      setBusy(false);
    }
  }

  return (
    // 100dvh minus header (4rem) minus bottom nav on mobile (4.5rem) so the input never hides behind the nav.
    <div className="mx-auto flex h-[calc(100dvh-4rem-4.5rem-3rem)] max-w-3xl flex-col lg:h-[calc(100dvh-4rem-4rem)]">
      <div className="mb-3">
        <p className="flex items-center gap-1.5 text-sm font-semibold text-brand-600"><Sparkles className="h-4 w-4" /> AI Tutor</p>
        <h1 className="font-display text-2xl font-extrabold text-ink">Ask a question</h1>
      </div>
      <div className="flex-1 space-y-3 overflow-y-auto rounded-3xl border border-line bg-white p-3 sm:p-4" aria-live="polite">
        {msgs.map((m, i) => (
          <div key={i} className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}>
            <div className={`max-w-[88%] whitespace-pre-line rounded-2xl px-4 py-2.5 text-sm leading-6 ${m.role === "user" ? "bg-brand-600 text-white" : "bg-mist text-ink"}`}>
              {m.text}
              {m.sources && m.sources.length > 0 && (
                <p className="mt-2 border-t border-line pt-1.5 text-[11px] text-muted">Sources: {m.sources.join(" · ")}</p>
              )}
            </div>
          </div>
        ))}
        {busy && <p className="text-sm text-muted">Thinking…</p>}
        <div ref={end} />
      </div>
      <div className="mt-2 flex gap-2 overflow-x-auto pb-1">
        {SUGGESTIONS.map((s) => (
          <button key={s} onClick={() => ask(s)} className="shrink-0 rounded-full border border-line bg-white px-3 py-2 text-xs font-medium text-muted hover:bg-mist">{s}</button>
        ))}
      </div>
      <form onSubmit={(e) => { e.preventDefault(); ask(text); }} className="mt-2 flex gap-2">
        <input value={text} onChange={(e) => setText(e.target.value)} placeholder="Type your question…" className="input-base" aria-label="Your question" maxLength={1000} />
        <button type="submit" disabled={busy || !text.trim()} className="flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl bg-brand-600 text-white disabled:opacity-50" aria-label="Send">
          <Send className="h-5 w-5" />
        </button>
      </form>
      <p className="mt-1 text-center text-[11px] text-muted">Answers come from your course material — verify important facts with your teacher.</p>
    </div>
  );
}
