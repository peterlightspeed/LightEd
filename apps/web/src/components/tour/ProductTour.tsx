"use client";

/**
 * Lightweight guided tour (no library).
 *
 * - A step points at an element via `data-tour="name"` (or a list of names tried in
 *   order — handy on mobile where the sidebar is hidden and the ☰ button is used).
 * - The target gets a spotlight (huge box-shadow trick) and a tooltip card.
 * - Steps with no visible target are shown as a centered card.
 * - Keyboard: → / Enter next, ← back, Esc close.
 */
import { useCallback, useEffect, useLayoutEffect, useState } from "react";
import { ArrowLeft, ArrowRight, X } from "lucide-react";

export interface TourStep {
  target?: string | string[];
  title: string;
  body: React.ReactNode;
}

/** First element for any of the names that is actually visible (non-zero size). */
function findTarget(target?: string | string[]): HTMLElement | null {
  if (!target) return null;
  for (const name of Array.isArray(target) ? target : [target]) {
    const els = document.querySelectorAll<HTMLElement>(`[data-tour="${name}"]`);
    for (const el of Array.from(els)) {
      const r = el.getBoundingClientRect();
      if (r.width > 0 && r.height > 0) return el;
    }
  }
  return null;
}

export default function ProductTour({
  steps,
  open,
  onClose,
}: {
  steps: TourStep[];
  open: boolean;
  onClose: () => void;
}) {
  const [index, setIndex] = useState(0);
  const [rect, setRect] = useState<DOMRect | null>(null);
  const step = steps[index];
  const last = index === steps.length - 1;

  const measure = useCallback(() => {
    const el = findTarget(step?.target);
    setRect(el ? el.getBoundingClientRect() : null);
  }, [step]);

  // Restart from step 1 every time the tour opens.
  useEffect(() => {
    if (open) setIndex(0);
  }, [open]);

  // Scroll the target into view, measure, and keep it measured on resize/scroll.
  useLayoutEffect(() => {
    if (!open) return;
    findTarget(step?.target)?.scrollIntoView({ block: "nearest", behavior: "auto" });
    measure();
    window.addEventListener("resize", measure);
    window.addEventListener("scroll", measure, true);
    return () => {
      window.removeEventListener("resize", measure);
      window.removeEventListener("scroll", measure, true);
    };
  }, [open, index, step, measure]);

  const next = useCallback(() => (last ? onClose() : setIndex((i) => i + 1)), [last, onClose]);
  const back = useCallback(() => setIndex((i) => Math.max(0, i - 1)), []);

  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
      else if (e.key === "ArrowRight" || e.key === "Enter") next();
      else if (e.key === "ArrowLeft") back();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open, next, back, onClose]);

  if (!open || !step) return null;

  /* ---- tooltip placement ---- */
  const vw = window.innerWidth;
  const vh = window.innerHeight;
  const width = Math.min(340, vw - 24);
  let style: React.CSSProperties;
  if (rect) {
    const sideways = rect.width < 320 && rect.left < 120 && vw >= 768; // sidebar items -> show on the right
    if (sideways) {
      style = { left: rect.right + 16, top: Math.min(Math.max(12, rect.top), vh - 260), width };
    } else {
      const below = rect.bottom + 14 + 230 < vh;
      style = {
        left: Math.min(Math.max(12, rect.left), vw - width - 12),
        top: below ? rect.bottom + 14 : Math.max(12, rect.top - 14 - 230),
        width,
      };
    }
  } else {
    style = { left: (vw - width) / 2, top: Math.max(16, vh / 2 - 130), width };
  }

  return (
    <div className="fixed inset-0 z-[100]" role="dialog" aria-modal="true" aria-label="Product tour">
      {/* Blocks clicks on the page while the tour is open. */}
      <div className="absolute inset-0" />
      {rect ? (
        <div
          className="pointer-events-none absolute rounded-2xl transition-all duration-300"
          style={{
            top: rect.top - 6,
            left: rect.left - 6,
            width: rect.width + 12,
            height: rect.height + 12,
            boxShadow: "0 0 0 9999px rgba(8, 20, 48, 0.65), 0 0 0 3px rgba(255, 191, 40, 0.9)",
          }}
        />
      ) : (
        <div className="absolute inset-0 bg-navy-900/65" />
      )}

      <div className="absolute rounded-2xl bg-white p-5 shadow-float" style={style}>
        <button
          onClick={onClose}
          className="absolute right-3 top-3 rounded-lg p-1 text-muted hover:bg-mist hover:text-ink"
          aria-label="Close tour"
        >
          <X className="h-4 w-4" />
        </button>
        <p className="text-[11px] font-bold uppercase tracking-wider text-brand-600">
          Step {index + 1} of {steps.length}
        </p>
        <h3 className="mt-1 pr-6 font-display text-lg font-extrabold text-ink">{step.title}</h3>
        <div className="mt-2 text-sm leading-6 text-muted">{step.body}</div>

        <div className="mt-4 flex items-center gap-1.5">
          {steps.map((_, i) => (
            <span key={i} className={`h-1.5 rounded-full transition-all ${i === index ? "w-5 bg-brand-500" : "w-1.5 bg-line"}`} />
          ))}
        </div>

        <div className="mt-4 flex items-center justify-between">
          <button onClick={onClose} className="text-xs font-semibold text-muted hover:text-ink">
            Skip tour
          </button>
          <div className="flex gap-2">
            {index > 0 && (
              <button onClick={back} className="inline-flex items-center gap-1 rounded-xl border border-line px-3 py-2 text-sm font-semibold text-ink hover:bg-mist">
                <ArrowLeft className="h-4 w-4" /> Back
              </button>
            )}
            <button onClick={next} className="inline-flex items-center gap-1 rounded-xl bg-brand-600 px-4 py-2 text-sm font-semibold text-white hover:bg-brand-700">
              {last ? "Done" : "Next"} {!last && <ArrowRight className="h-4 w-4" />}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
