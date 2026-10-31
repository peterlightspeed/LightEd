"use client";

/**
 * AI tutor chat. Answers come ONLY from the user's course material and always cite sources.
 *
 * Mobile notes
 *  - On phones the chat is pinned between the top bar and the bottom tab bar (fixed insets, not a
 *    calc() height), so the composer is always reachable and never hides behind the tab bar.
 *  - Scrolling uses the message list's own scrollTo(). No effect returns a value: React treats any
 *    non-function return from useEffect as a cleanup and crashes the whole page if it isn't one.
 */
import { useCallback, useEffect, useRef, useState } from "react";
import { AlertCircle, BookOpen, RotateCcw, Send, Sparkles } from "lucide-react";

import { api } from "@/lib/api";
import { useSlowHint } from "@/lib/hooks";
import { RichText } from "@/lib/richtext";

interface Msg {
  role: "user" | "tutor";
  text: string;
  sources?: string[];
  notice?: string | null;
  error?: boolean;
}
interface Reply {
  answer: string;
  sources: string[];
  provider?: string;
  notice?: string | null;
}

const STORE = "lighted_tutor_chat_v1";
const GREETING: Msg = {
  role: "tutor",
  text: "Hi! Ask me anything about your enrolled courses. I answer from your lesson material and show where it came from.",
};
const STARTERS = ["What should I focus on first?", "Summarise my latest lesson", "Quiz me with one question"];
const FOLLOW_UPS = ["Explain this in simple words", "Give me an example", "Quiz me on this"];

export default function TutorPage() {
  const [msgs, setMsgs] = useState<Msg[]>([GREETING]);
  const [text, setText] = useState("");
  const [busy, setBusy] = useState(false);
  const list = useRef<HTMLDivElement>(null);
  const box = useRef<HTMLTextAreaElement>(null);
  const slow = useSlowHint(busy, 6000);
  const started = msgs.length > 1;

  // Restore this tab's conversation after a refresh (sessionStorage = cleared when the tab closes).
  useEffect(() => {
    try {
      const saved = sessionStorage.getItem(STORE);
      if (saved) {
        const parsed = JSON.parse(saved) as Msg[];
        if (Array.isArray(parsed) && parsed.length) setMsgs(parsed);
      }
    } catch {
      /* storage blocked or corrupt: start fresh */
    }
  }, []);

  useEffect(() => {
    try {
      sessionStorage.setItem(STORE, JSON.stringify(msgs.slice(-30)));
    } catch {
      /* ignore */
    }
  }, [msgs]);

  // Keep the newest message in view. Block body on purpose: nothing may be returned from an effect.
  useEffect(() => {
    const el = list.current;
    if (!el) return;
    const reduce = window.matchMedia?.("(prefers-reduced-motion: reduce)").matches;
    el.scrollTo({ top: el.scrollHeight, behavior: reduce ? "auto" : "smooth" });
  }, [msgs, busy]);

  // Auto-grow the composer up to ~5 lines.
  useEffect(() => {
    const t = box.current;
    if (!t) return;
    t.style.height = "auto";
    t.style.height = `${Math.min(t.scrollHeight, 132)}px`;
  }, [text]);

  const ask = useCallback(
    async (raw: string, opts: { retry?: boolean } = {}) => {
      const q = raw.trim();
      if (!q || busy) return;
      // Context for follow-ups like "give me an example": the last few real turns (no errors/greeting).
      const real = msgs.filter((m) => !m.error && m.text !== GREETING.text);
      // On retry the question is already the last real turn, so don't send it twice.
      const history = (opts.retry ? real.slice(0, -1) : real)
        .slice(-6)
        .map((m) => ({ role: m.role, text: m.text.slice(0, 1500) }));
      setMsgs((m) => (opts.retry ? m.filter((x) => !x.error) : [...m, { role: "user", text: q }]));
      setText("");
      setBusy(true);
      try {
        // retry=true: the free-tier API may be asleep; this call is safe to repeat.
        const r = await api.post<Reply>("/ai/tutor", { question: q, history }, true, true);
        setMsgs((m) => [...m, { role: "tutor", text: r.answer, sources: r.sources, notice: r.notice }]);
      } catch (err) {
        setMsgs((m) => [
          ...m,
          { role: "tutor", error: true, text: err instanceof Error ? err.message : "Sorry, I couldn't answer that." },
        ]);
      } finally {
        setBusy(false);
      }
    },
    [busy, msgs]
  );

  const lastQuestion = [...msgs].reverse().find((m) => m.role === "user")?.text;

  function reset() {
    setMsgs([GREETING]);
    setText("");
    try {
      sessionStorage.removeItem(STORE);
    } catch {
      /* ignore */
    }
  }

  return (
    <div className="fixed inset-x-0 top-16 bottom-[calc(3.75rem+env(safe-area-inset-bottom))] z-10 flex flex-col bg-mist px-3 pb-2 pt-2 sm:px-6 lg:static lg:z-auto lg:mx-auto lg:h-[calc(100dvh-8rem)] lg:max-w-3xl lg:bg-transparent lg:p-0">
      <div className="mb-2 flex items-center justify-between gap-3 lg:mb-3">
        <div className="min-w-0">
          <p className="hidden items-center gap-1.5 text-sm font-semibold text-brand-600 lg:flex">
            <Sparkles className="h-4 w-4" /> AI Tutor
          </p>
          <h1 className="flex items-center gap-2 font-display text-lg font-extrabold text-ink lg:text-2xl">
            <Sparkles className="h-5 w-5 text-brand-600 lg:hidden" aria-hidden />
            <span className="truncate">Ask a question</span>
          </h1>
        </div>
        {started && (
          <button
            onClick={reset}
            className="flex h-11 shrink-0 items-center gap-1.5 rounded-xl px-3 text-sm font-semibold text-muted hover:bg-white hover:text-ink"
            aria-label="Start a new chat"
          >
            <RotateCcw className="h-4 w-4" /> New chat
          </button>
        )}
      </div>

      <div
        ref={list}
        role="log"
        aria-live="polite"
        aria-label="Conversation with your AI tutor"
        className="min-h-0 flex-1 space-y-3 overflow-y-auto overscroll-contain rounded-3xl border border-line bg-white p-3 sm:p-4"
      >
        {msgs.map((m, i) => (
          <div key={i} className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}>
            <div
              className={`max-w-[92%] rounded-2xl px-4 py-2.5 text-[15px] leading-6 sm:max-w-[85%] ${
                m.role === "user"
                  ? "rounded-br-md bg-brand-600 text-white"
                  : m.error
                    ? "rounded-bl-md border border-rose-200 bg-rose-50 text-rose-700"
                    : "rounded-bl-md bg-mist text-ink"
              }`}
            >
              {m.error && (
                <p className="mb-1 flex items-center gap-1.5 text-xs font-bold">
                  <AlertCircle className="h-3.5 w-3.5" /> Couldn&apos;t get an answer
                </p>
              )}
              {m.role === "tutor" && !m.error ? <RichText text={m.text} /> : <p className="whitespace-pre-line">{m.text}</p>}

              {m.notice && (
                <p className="mt-2 rounded-lg bg-amber-50 px-2.5 py-1.5 text-xs leading-5 text-amber-800">{m.notice}</p>
              )}
              {m.sources && m.sources.length > 0 && (
                <div className="mt-2.5 border-t border-line pt-2">
                  <p className="mb-1.5 text-[11px] font-semibold text-muted">From your course material</p>
                  <ul className="flex flex-wrap gap-1.5">
                    {m.sources.map((s) => (
                      <li key={s} className="inline-flex max-w-full items-center gap-1 rounded-full bg-white px-2.5 py-1 text-[11px] font-medium text-navy-700">
                        <BookOpen className="h-3 w-3 shrink-0 text-brand-600" aria-hidden />
                        <span className="truncate">{s}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
              {m.error && lastQuestion && i === msgs.length - 1 && (
                <button
                  onClick={() => ask(lastQuestion, { retry: true })}
                  disabled={busy}
                  className="mt-2 inline-flex min-h-[40px] items-center gap-1.5 rounded-xl bg-rose-600 px-3.5 text-sm font-semibold text-white disabled:opacity-60"
                >
                  <RotateCcw className="h-4 w-4" /> Try again
                </button>
              )}
            </div>
          </div>
        ))}

        {!started && !busy && (
          <div className="grid gap-2 pt-1">
            <p className="px-1 text-xs font-semibold text-muted">Try asking</p>
            {STARTERS.map((s) => (
              <button
                key={s}
                onClick={() => ask(s)}
                className="min-h-[48px] rounded-2xl border border-line bg-white px-4 text-left text-sm font-medium text-ink transition hover:border-brand-300 hover:bg-brand-50 active:bg-brand-50"
              >
                {s}
              </button>
            ))}
          </div>
        )}

        {busy && (
          <div className="flex justify-start" role="status" aria-label="Tutor is thinking">
            <div className="rounded-2xl rounded-bl-md bg-mist px-4 py-3">
              <span className="flex items-center gap-1" aria-hidden>
                {[0, 150, 300].map((d) => (
                  <span key={d} className="h-2 w-2 rounded-full bg-muted/60 motion-safe:animate-bounce" style={{ animationDelay: `${d}ms` }} />
                ))}
              </span>
              {slow && <p className="mt-2 text-xs text-muted">The server is waking up. This can take up to a minute the first time.</p>}
            </div>
          </div>
        )}
      </div>

      {started && (
        <div
          className="-mx-3 mt-2 flex gap-2 overflow-x-auto px-3 pb-1 sm:mx-0 sm:px-0 [scrollbar-width:none] [&::-webkit-scrollbar]:hidden"
          aria-label="Suggested follow-ups"
        >
          {FOLLOW_UPS.map((s) => (
            <button
              key={s}
              onClick={() => ask(s)}
              disabled={busy}
              className="min-h-[40px] shrink-0 rounded-full border border-line bg-white px-3.5 text-xs font-semibold text-muted transition hover:bg-brand-50 hover:text-brand-700 disabled:opacity-50"
            >
              {s}
            </button>
          ))}
        </div>
      )}

      <form
        onSubmit={(e) => {
          e.preventDefault();
          ask(text);
        }}
        className="mt-2 flex items-end gap-2"
      >
        <textarea
          ref={box}
          rows={1}
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={(e) => {
            // Enter sends, Shift+Enter adds a new line. Ignore Enter while an IME is composing.
            if (e.key === "Enter" && !e.shiftKey && !e.nativeEvent.isComposing) {
              e.preventDefault();
              ask(text);
            }
          }}
          enterKeyHint="send"
          placeholder="Type your question…"
          aria-label="Your question"
          maxLength={1000}
          className="input-base max-h-[132px] min-h-[48px] resize-none py-3 leading-6"
        />
        <button
          type="submit"
          disabled={busy || !text.trim()}
          className="flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl bg-brand-600 text-white transition hover:bg-brand-700 active:scale-95 disabled:opacity-50"
          aria-label="Send question"
        >
          <Send className="h-5 w-5" />
        </button>
      </form>
      <p className="mt-1.5 hidden text-center text-[11px] text-muted sm:block">
        Answers come from your course material. Verify important facts with your teacher.
      </p>
    </div>
  );
}
