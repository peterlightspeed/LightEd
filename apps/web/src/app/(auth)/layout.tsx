import Link from "next/link";
import { CheckCircle2, Sparkles } from "lucide-react";

import { Logo } from "@/components/ui";

/**
 * Split-screen auth layout inspired by the Figma auth flow:
 * deep navy brand panel on the left, white form card on the right.
 */
export default function AuthLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex min-h-screen bg-white">
      {/* Brand panel */}
      <aside className="relative hidden w-[46%] flex-col justify-between overflow-hidden bg-navy-700 p-12 lg:flex">
        <div className="absolute -right-24 -top-24 h-80 w-80 rounded-full bg-brand-500/30 blur-3xl" />
        <div className="absolute -bottom-32 -left-20 h-96 w-96 rounded-full bg-gold-400/20 blur-3xl" />

        <Link href="/" className="relative">
          <Logo variant="light" />
        </Link>

        <div className="relative max-w-md">
          <span className="inline-flex items-center gap-2 rounded-full bg-white/10 px-3 py-1.5 text-xs font-semibold text-gold-300">
            <Sparkles className="h-3.5 w-3.5" /> AI-assisted learning
          </span>
          <h1 className="mt-6 font-display text-4xl font-extrabold leading-tight text-white">
            Light yourself.
            <br />
            <span className="text-gold-300">Learn at your pace.</span>
          </h1>
          <p className="mt-4 text-sm leading-6 text-white/70">
            Personalized lessons, instant quizzes and progress insights that help every
            student move forward — and every teacher see where to help.
          </p>

          <ul className="mt-8 space-y-3">
            {[
              "Lessons that adapt to your strengths",
              "Instant quiz feedback with explanations",
              "Clear progress for students and teachers",
            ].map((item) => (
              <li key={item} className="flex items-center gap-3 text-sm text-white/80">
                <CheckCircle2 className="h-4 w-4 shrink-0 text-gold-300" />
                {item}
              </li>
            ))}
          </ul>
        </div>

        <p className="relative text-xs text-white/40">
          © {new Date().getFullYear()} LightEd · TechCrush Buildathon MVP
        </p>
      </aside>

      {/* Form panel */}
      <main className="flex w-full flex-col lg:w-[54%]">
        <div className="flex items-center justify-between px-6 py-5 lg:px-12">
          <Link href="/" className="lg:hidden">
            <Logo />
          </Link>
          <Link href="/" className="ml-auto text-sm font-medium text-muted hover:text-ink">
            ← Back to home
          </Link>
        </div>
        <div className="flex flex-1 items-center justify-center px-6 pb-12 lg:px-12">
          <div className="w-full max-w-md">{children}</div>
        </div>
      </main>
    </div>
  );
}
