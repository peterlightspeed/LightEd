"use client";

/** Getting-started guide for teachers: the 5 steps, plus where to find free teaching material. Dismissible. */
import { useEffect, useState } from "react";
import Link from "next/link";
import { BookOpenCheck, ExternalLink, X } from "lucide-react";

import { Card } from "@/components/ui";

const KEY = "lighted_teacher_guide_hidden";

const STEPS = [
  { t: "Create a course", d: "Give it a clear title and a short description of what students will learn.", href: "/courses?new=1" },
  { t: "Add topics", d: "Topics are chapters. Tap “Suggest topics” and the AI will propose an outline." },
  { t: "Add lessons", d: "Type, paste, or import text from a PDF. Tap “Draft with AI” for a first version, then edit it." },
  { t: "Add videos and recordings", d: "Under “Quiz & links” paste a YouTube, Instagram or Zoom/Meet recording link. YouTube and Instagram play inside the lesson." },
  { t: "Publish a quiz and share your class code", d: "Generate a quiz from the lesson, publish it, then give students the 6-character class code." },
];

const SOURCES = [
  { n: "OpenStax", u: "https://openstax.org", d: "Free textbooks" },
  { n: "Khan Academy", u: "https://www.khanacademy.org", d: "Lessons and exercises" },
  { n: "MIT OpenCourseWare", u: "https://ocw.mit.edu", d: "University course notes" },
  { n: "OER Commons", u: "https://oercommons.org", d: "Open teaching resources" },
  { n: "Wikibooks", u: "https://www.wikibooks.org", d: "Open textbooks" },
];

export default function TeacherGuide() {
  const [hidden, setHidden] = useState(false);
  useEffect(() => {
    try {
      setHidden(localStorage.getItem(KEY) === "1");
    } catch {
      /* storage blocked: keep it visible */
    }
  }, []);

  function setFlag(v: boolean) {
    setHidden(v);
    try {
      localStorage.setItem(KEY, v ? "1" : "0");
    } catch {
      /* ignore */
    }
  }

  if (hidden) {
    return (
      <button onClick={() => setFlag(false)} className="inline-flex min-h-[44px] items-center gap-2 text-sm font-semibold text-brand-600">
        <BookOpenCheck className="h-4 w-4" /> Show the getting-started guide
      </button>
    );
  }

  return (
    <Card className="p-5 sm:p-6">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="flex items-center gap-2 font-display text-lg font-bold text-ink"><BookOpenCheck className="h-5 w-5 text-brand-600" /> Getting started as a teacher</p>
          <p className="mt-0.5 text-sm text-muted">Five steps from an empty course to students learning.</p>
        </div>
        <button onClick={() => setFlag(true)} className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl text-muted hover:bg-mist" aria-label="Hide the guide">
          <X className="h-5 w-5" />
        </button>
      </div>
      <ol className="mt-4 space-y-3">
        {STEPS.map((s, i) => (
          <li key={s.t} className="flex gap-3">
            <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-brand-50 text-sm font-bold text-brand-700">{i + 1}</span>
            <p className="text-sm text-muted">
              {s.href ? <Link href={s.href} className="font-semibold text-brand-600 hover:underline">{s.t}</Link> : <span className="font-semibold text-ink">{s.t}</span>}
              <span>. {s.d}</span>
            </p>
          </li>
        ))}
      </ol>
      <div className="mt-5 rounded-2xl bg-mist/70 p-4">
        <p className="text-sm font-semibold text-ink">Where to find free teaching material</p>
        <ul className="mt-2 grid gap-1 sm:grid-cols-2">
          {SOURCES.map((s) => (
            <li key={s.n}>
              <a href={s.u} target="_blank" rel="noopener noreferrer" className="flex min-h-[44px] items-center justify-between gap-2 text-sm font-medium text-brand-600">
                <span>{s.n} <span className="font-normal text-muted">· {s.d}</span></span>
                <ExternalLink className="h-3.5 w-3.5 shrink-0" />
              </a>
            </li>
          ))}
        </ul>
        <p className="mt-2 text-xs text-muted">Always check each resource&apos;s licence before reusing it, and credit the author. You can also ask the AI Tutor for help.</p>
      </div>
    </Card>
  );
}
