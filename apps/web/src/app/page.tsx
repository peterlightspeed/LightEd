/**
 * Marketing landing page.
 *
 * This is the public entry point (no auth required). It mirrors the Figma
 * direction: deep navy hero, bright blue CTA, floating "progress" cards, and
 * three simple story sections (features, how it works, for teachers).
 */
import Link from "next/link";
import {
  ArrowRight,
  BarChart3,
  BookOpen,
  Brain,
  CheckCircle2,
  GraduationCap,
  LineChart,
  PlayCircle,
  Sparkles,
  Target,
  Users,
} from "lucide-react";

import ContactSection from "@/components/marketing/ContactSection";
import Footer from "@/components/marketing/Footer";
import MarketingNav from "@/components/marketing/MarketingNav";
import { Badge, ButtonLink, Card, ProgressBar } from "@/components/ui";

/* Small helper so the section headers stay consistent. */
function SectionHeading({
  eyebrow,
  title,
  description,
  center = false,
}: {
  eyebrow: string;
  title: string;
  description?: string;
  center?: boolean;
}) {
  return (
    <div className={center ? "mx-auto max-w-2xl text-center" : "max-w-2xl"}>
      <p className="eyebrow">{eyebrow}</p>
      <h2 className="mt-3 font-display text-3xl font-extrabold tracking-tight text-ink sm:text-4xl">{title}</h2>
      {description && <p className="mt-4 text-base leading-7 text-muted">{description}</p>}
    </div>
  );
}

const features = [
  {
    icon: Brain,
    title: "AI study companion",
    body: "Ask for a simpler explanation, a worked example, or a quick recap. The tutor adapts to the lesson you are on.",
    tone: "bg-brand-50 text-brand-600",
  },
  {
    icon: Target,
    title: "Personalised paths",
    body: "LightEd spots the topics you are shaky on and lines up the next lesson that actually moves you forward.",
    tone: "bg-emerald-50 text-emerald-600",
  },
  {
    icon: LineChart,
    title: "Progress you can see",
    body: "A single progress ring, weekly activity, and per-course mastery so you always know where you stand.",
    tone: "bg-amber-50 text-amber-600",
  },
  {
    icon: BookOpen,
    title: "Structured courses",
    body: "Every course is split into topics, lessons, and short quizzes so learning feels like a clear path, not a pile of links.",
    tone: "bg-violet-50 text-violet-600",
  },
];

const steps = [
  {
    step: "01",
    title: "Pick your goal",
    body: "Choose a course that matches where you are headed. Enrol in one click and see the whole curriculum up front.",
  },
  {
    step: "02",
    title: "Learn a little every day",
    body: "Read short lessons, mark them complete, and check your understanding with a quick quiz at the end of each one.",
  },
  {
    step: "03",
    title: "Watch the ring fill up",
    body: "Your dashboard turns completed lessons and quiz scores into a clear picture of progress and next steps.",
  },
];

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-white">
      <MarketingNav />

      {/* ------------------------------------------------------------ Hero */}
      <section className="relative overflow-hidden">
        {/* Soft background glow, keeps the hero from feeling flat. */}
        <div className="pointer-events-none absolute -right-40 -top-40 h-[520px] w-[520px] rounded-full bg-brand-100/60 blur-3xl" />
        <div className="pointer-events-none absolute -left-32 top-40 h-[360px] w-[360px] rounded-full bg-gold-100/60 blur-3xl" />

        <div className="container-page relative grid items-center gap-14 py-16 lg:grid-cols-[1.05fr_0.95fr] lg:py-24">
          <div>
            <Badge tone="blue" className="mb-5">
              <Sparkles className="h-3.5 w-3.5" />
              AI-assisted learning, built for real classrooms
            </Badge>
            <h1 className="font-display text-4xl font-extrabold leading-[1.08] tracking-tight text-ink sm:text-5xl lg:text-6xl">
              Light yourself.
              <br />
              <span className="text-brand-500">Learn at your pace.</span>
            </h1>
            <p className="mt-6 max-w-xl text-lg leading-8 text-muted">
              LightEd blends structured courses with an AI study companion, so every learner gets a clear
              next step and every teacher gets a live view of who needs help.
            </p>

            <div className="mt-8 flex flex-col gap-3 sm:flex-row">
              <ButtonLink href="/register" size="lg">
                Start learning free
                <ArrowRight className="h-4 w-4" />
              </ButtonLink>
              <ButtonLink href="/login" variant="secondary" size="lg">
                <PlayCircle className="h-4 w-4" />
                Explore the demo
              </ButtonLink>
            </div>

            <div className="mt-8 flex flex-wrap items-center gap-x-6 gap-y-3 text-sm text-muted">
              {["No credit card", "Student & teacher accounts", "Works on any device"].map((item) => (
                <span key={item} className="inline-flex items-center gap-2">
                  <CheckCircle2 className="h-4 w-4 text-emerald-500" />
                  {item}
                </span>
              ))}
            </div>
          </div>

          {/* Hero "product" preview: a stylised dashboard card. */}
          <div className="relative">
            <div className="absolute -inset-4 rounded-[2.5rem] bg-gradient-to-br from-brand-500/10 to-gold-300/20 blur-2xl" />
            <Card className="relative overflow-hidden rounded-[2rem] border-line/70 p-6 shadow-float">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-xs font-semibold uppercase tracking-widest text-muted">Your week</p>
                  <p className="mt-1 font-display text-xl font-bold text-ink">Good morning, Sam</p>
                </div>
                <span className="flex h-11 w-11 items-center justify-center rounded-2xl bg-navy-700 text-white">
                  <GraduationCap className="h-5 w-5" />
                </span>
              </div>

              <div className="mt-6 grid grid-cols-3 gap-3">
                {[
                  { label: "Courses", value: "3" },
                  { label: "Lessons", value: "7" },
                  { label: "Avg score", value: "78%" },
                ].map((stat) => (
                  <div key={stat.label} className="rounded-2xl bg-mist p-3 text-center">
                    <p className="font-display text-lg font-extrabold text-ink">{stat.value}</p>
                    <p className="text-[11px] font-medium text-muted">{stat.label}</p>
                  </div>
                ))}
              </div>

              <div className="mt-5 rounded-2xl border border-line/70 p-4">
                <div className="flex items-center justify-between text-sm">
                  <span className="font-semibold text-ink">Algebra Foundations</span>
                  <span className="text-muted">75%</span>
                </div>
                <ProgressBar value={75} className="mt-2" />
                <div className="mt-4 flex items-center justify-between text-sm">
                  <span className="font-semibold text-ink">Biology: Cells to Systems</span>
                  <span className="text-muted">66%</span>
                </div>
                <ProgressBar value={66} className="mt-2" barClassName="bg-emerald-500" />
              </div>

              <div className="mt-5 flex items-start gap-3 rounded-2xl bg-brand-500 p-4 text-white">
                <Sparkles className="mt-0.5 h-5 w-5 text-gold-300" />
                <div>
                  <p className="text-sm font-bold">AI Tutor</p>
                  <p className="text-xs leading-5 text-white/80">
                    &ldquo;Explain the quadratic formula like I&apos;m new to it.&rdquo;
                  </p>
                </div>
              </div>
            </Card>

            {/* Floating accent badge for depth. */}
            <div className="absolute -bottom-5 -left-5 hidden rounded-2xl bg-white p-4 shadow-float sm:block">
              <div className="flex items-center gap-3">
                <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-emerald-50 text-emerald-600">
                  <BarChart3 className="h-5 w-5" />
                </span>
                <div>
                  <p className="text-xs text-muted">This month</p>
                  <p className="text-sm font-bold text-ink">+12 lessons completed</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* -------------------------------------------------------- Features */}
      <section id="features" className="border-t border-line/60 bg-mist/60 py-20">
        <div className="container-page">
          <SectionHeading
            eyebrow="Why LightEd"
            title="Everything a learner needs, in one calm place"
            description="We stripped out the noise. What is left is a focused loop: learn a lesson, check your understanding, see your progress grow."
            center
          />

          <div className="mt-12 grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
            {features.map((feature) => {
              const Icon = feature.icon;
              return (
                <Card key={feature.title} className="h-full p-6 transition hover:-translate-y-1 hover:shadow-float">
                  <span className={`flex h-12 w-12 items-center justify-center rounded-2xl ${feature.tone}`}>
                    <Icon className="h-6 w-6" />
                  </span>
                  <h3 className="mt-5 font-display text-lg font-bold text-ink">{feature.title}</h3>
                  <p className="mt-2 text-sm leading-6 text-muted">{feature.body}</p>
                </Card>
              );
            })}
          </div>
        </div>
      </section>

      {/* ---------------------------------------------------- How it works */}
      <section id="how-it-works" className="py-20">
        <div className="container-page grid gap-14 lg:grid-cols-[0.9fr_1.1fr] lg:items-center">
          <div>
            <SectionHeading
              eyebrow="How it works"
              title="A simple loop that keeps you moving"
              description="No overwhelming dashboards. LightEd shows one next step at a time and makes finishing it feel good."
            />
            <div className="mt-8 space-y-6">
              {steps.map((step) => (
                <div key={step.step} className="flex gap-4">
                  <span className="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl bg-navy-700 font-display text-sm font-bold text-white">
                    {step.step}
                  </span>
                  <div>
                    <h3 className="font-display text-base font-bold text-ink">{step.title}</h3>
                    <p className="mt-1 text-sm leading-6 text-muted">{step.body}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <Card className="relative overflow-hidden rounded-[2rem] bg-navy-700 p-8 text-white">
            <div className="pointer-events-none absolute -right-16 -top-16 h-56 w-56 rounded-full bg-brand-500/30 blur-2xl" />
            <p className="text-xs font-bold uppercase tracking-[0.2em] text-gold-300">Lesson view</p>
            <h3 className="mt-3 font-display text-2xl font-extrabold">Solving linear equations</h3>
            <p className="mt-2 text-sm text-white/60">Algebra Foundations · Topic 2 · 12 min</p>

            <div className="mt-6 space-y-3 rounded-2xl bg-white/10 p-5 text-sm leading-6 text-white/85">
              <p>
                An equation is a balance. Whatever you do to one side, you must do to the other. To isolate
                <span className="mx-1 rounded bg-white/15 px-1.5 py-0.5 font-mono text-xs">x</span>, undo the
                operations around it in reverse order.
              </p>
              <p className="rounded-xl bg-white/10 p-3 font-mono text-xs text-gold-200">
                2x + 3 = 11 → 2x = 8 → x = 4
              </p>
            </div>

            <div className="mt-6 flex items-center justify-between rounded-2xl bg-white p-4 text-ink">
              <div>
                <p className="text-xs text-muted">Up next</p>
                <p className="text-sm font-bold">Quick check: linear equations</p>
              </div>
              <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-brand-500 text-white">
                <ArrowRight className="h-5 w-5" />
              </span>
            </div>
          </Card>
        </div>
      </section>

      {/* ----------------------------------------------------- For teachers */}
      <section id="for-teachers" className="border-y border-line/60 bg-mist/60 py-20">
        <div className="container-page grid gap-12 lg:grid-cols-2 lg:items-center">
          <Card className="order-2 rounded-[2rem] p-7 lg:order-1">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs font-semibold uppercase tracking-widest text-muted">Class overview</p>
                <p className="mt-1 font-display text-xl font-bold text-ink">Algebra Foundations</p>
              </div>
              <Badge tone="green">On track</Badge>
            </div>
            <div className="mt-6 space-y-4">
              {[
                { name: "Sam Rivera", score: 78, status: "on_track" },
                { name: "Maya Chen", score: 91, status: "on_track" },
                { name: "Noah Patel", score: 48, status: "at_risk" },
              ].map((student) => (
                <div key={student.name} className="flex items-center gap-3">
                  <span className="flex h-9 w-9 items-center justify-center rounded-full bg-navy-700 text-xs font-bold text-white">
                    {student.name.split(" ").map((n) => n[0]).join("")}
                  </span>
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center justify-between text-sm">
                      <span className="font-semibold text-ink">{student.name}</span>
                      <span className={student.status === "at_risk" ? "text-rose-600" : "text-muted"}>
                        {student.score}%
                      </span>
                    </div>
                    <ProgressBar
                      value={student.score}
                      size="sm"
                      className="mt-1.5"
                      barClassName={student.status === "at_risk" ? "bg-rose-500" : "bg-emerald-500"}
                    />
                  </div>
                </div>
              ))}
            </div>
          </Card>

          <div className="order-1 lg:order-2">
            <SectionHeading
              eyebrow="For teachers"
              title="See who is thriving and who needs a nudge"
              description="Class averages, per-course progress, and at-risk flags are calculated from real lesson and quiz activity, not guesswork."
            />
            <ul className="mt-6 space-y-3">
              {[
                "Track lesson completion across every enrolled student",
                "Spot at-risk learners before the next assessment",
                "Publish courses and manage your curriculum from one place",
              ].map((item) => (
                <li key={item} className="flex items-start gap-3 text-sm text-ink">
                  <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-emerald-500" />
                  {item}
                </li>
              ))}
            </ul>
            <div className="mt-8 flex flex-wrap gap-3">
              <ButtonLink href="/register" size="lg">
                <Users className="h-4 w-4" />
                Create a teacher account
              </ButtonLink>
              <ButtonLink href="/login" variant="secondary" size="lg">
                Sign in
              </ButtonLink>
            </div>
          </div>
        </div>
      </section>

      {/* -------------------------------------------------------------- CTA */}
      <section className="py-20">
        <div className="container-page">
          <div className="relative overflow-hidden rounded-[2.5rem] bg-navy-700 px-8 py-14 text-center text-white sm:px-16">
            <div className="pointer-events-none absolute -left-20 -top-20 h-64 w-64 rounded-full bg-brand-500/30 blur-3xl" />
            <div className="pointer-events-none absolute -bottom-24 -right-16 h-64 w-64 rounded-full bg-gold-400/20 blur-3xl" />
            <div className="relative mx-auto max-w-2xl">
              <h2 className="font-display text-3xl font-extrabold sm:text-4xl">Ready to light up your learning?</h2>
              <p className="mt-4 text-base leading-7 text-white/70">
                Create a free account and start with a course that fits your goals. Your first lesson is
                waiting.
              </p>
              <div className="mt-8 flex flex-col justify-center gap-3 sm:flex-row">
                <ButtonLink href="/register" variant="gold" size="lg">
                  Get started free
                  <ArrowRight className="h-4 w-4" />
                </ButtonLink>
                <Link
                  href="/login"
                  className="inline-flex h-12 items-center justify-center rounded-2xl border border-white/25 px-6 text-[15px] font-semibold text-white transition hover:bg-white/10"
                >
                  I already have an account
                </Link>
              </div>
            </div>
          </div>
        </div>
      </section>

      <ContactSection />
      <Footer />
    </div>
  );
}
