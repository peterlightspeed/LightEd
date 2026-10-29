/**
 * Marketing landing page.
 *
 * This is the public entry point (no auth required). It mirrors the Figma
 * direction: deep navy hero, bright blue CTA, floating "progress" cards, and
 * a short, ordered story: who it is for -> how it works -> what you get -> sign up.
 * (No in-page section links: the sections are short enough to just scroll.)
 */
import Link from "next/link";
import {
  ArrowRight,
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

import { AvatarGroup, StudentScene, TeacherScene } from "@/components/illustrations/People";
import Footer from "@/components/marketing/Footer";
import MarketingNav from "@/components/marketing/MarketingNav";
import { Badge, ButtonLink, Card } from "@/components/ui";

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
        <div className="pointer-events-none absolute -right-40 -top-40 h-[520px] w-[520px] rounded-full bg-brand-100/60 blur-3xl" />
        <div className="pointer-events-none absolute -left-32 top-40 h-[360px] w-[360px] rounded-full bg-gold-100/60 blur-3xl" />

        <div className="container-page relative grid items-center gap-10 py-12 lg:grid-cols-[1.05fr_0.95fr] lg:py-20">
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
              LightEd pairs structured courses with an AI study companion, so every learner gets a clear next step and
              every teacher can see who needs help.
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

            <div className="mt-8 flex items-center gap-4">
              <AvatarGroup />
              <p className="text-sm font-medium text-muted">For students, teachers and schools</p>
            </div>
            <ul className="mt-5 flex flex-wrap gap-x-6 gap-y-2 text-sm text-muted">
              {["No credit card", "Student & teacher accounts", "Works on any device"].map((t) => (
                <li key={t} className="flex items-center gap-2">
                  <CheckCircle2 className="h-4 w-4 text-emerald-500" /> {t}
                </li>
              ))}
            </ul>
          </div>

          <StudentScene className="mx-auto w-full max-w-[520px]" />
        </div>
      </section>

      {/* ------------------------------------------------------------ Who it is for (students + teachers together) */}
      <section className="border-y border-line/60 bg-mist/60 py-16 sm:py-20">
        <div className="container-page">
          <SectionHeading
            center
            eyebrow="Made for people"
            title="One platform, two ways to win"
            description="Learners get guidance. Teachers get visibility. Both save time."
          />
          <div className="mt-12 grid gap-6 lg:grid-cols-2">
            <Card className="overflow-hidden !p-0">
              <div className="bg-brand-50 px-6 pt-6">
                <StudentScene className="mx-auto h-48 w-auto" />
              </div>
              <div className="p-6 sm:p-8">
                <Badge tone="blue"><GraduationCap className="h-3.5 w-3.5" /> For students</Badge>
                <h3 className="mt-3 font-display text-2xl font-extrabold text-ink">Know exactly what to study next</h3>
                <ul className="mt-4 space-y-2.5 text-sm text-muted">
                  {["Short lessons and instant quizzes", "An AI tutor that answers from your course and shows its sources", "A revision plan built around your weak topics", "Your own progress, always one tap away"].map((t) => (
                    <li key={t} className="flex gap-2.5"><CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-emerald-500" />{t}</li>
                  ))}
                </ul>
                <ButtonLink href="/register" className="mt-6">Join as a student <ArrowRight className="h-4 w-4" /></ButtonLink>
              </div>
            </Card>

            <Card className="overflow-hidden !p-0">
              <div className="bg-gold-100/70 px-6 pt-6">
                <TeacherScene className="mx-auto h-48 w-auto" />
              </div>
              <div className="p-6 sm:p-8">
                <Badge tone="amber"><Users className="h-3.5 w-3.5" /> For teachers</Badge>
                <h3 className="mt-3 font-display text-2xl font-extrabold text-ink">See who needs help, early</h3>
                <ul className="mt-4 space-y-2.5 text-sm text-muted">
                  {["Build courses, lessons and quizzes in minutes", "AI drafts quizzes; you review and approve before students see them", "Class code to enrol your students instantly", "Early-warning view of your own students, with the reasons"].map((t) => (
                    <li key={t} className="flex gap-2.5"><CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-emerald-500" />{t}</li>
                  ))}
                </ul>
                <ButtonLink href="/register" variant="secondary" className="mt-6">Join as a teacher <ArrowRight className="h-4 w-4" /></ButtonLink>
              </div>
            </Card>
          </div>
        </div>
      </section>

      {/* ------------------------------------------------------------ How it works */}
      <section className="py-16 sm:py-20">
        <div className="container-page">
          <SectionHeading center eyebrow="How it works" title="From first lesson to real progress" />
          <div className="mt-12 grid gap-6 md:grid-cols-3">
            {steps.map((s) => (
              <Card key={s.step}>
                <span className="font-display text-4xl font-extrabold text-brand-100">{s.step}</span>
                <h3 className="mt-2 font-display text-xl font-bold text-ink">{s.title}</h3>
                <p className="mt-2 text-sm leading-6 text-muted">{s.body}</p>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* ------------------------------------------------------------ Features */}
      <section className="border-t border-line/60 bg-mist/60 py-16 sm:py-20">
        <div className="container-page">
          <SectionHeading center eyebrow="What you get" title="Everything you need, nothing you don't" />
          <div className="mt-12 grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
            {features.map((f) => (
              <Card key={f.title}>
                <span className={`flex h-11 w-11 items-center justify-center rounded-2xl ${f.tone}`}>
                  <f.icon className="h-5 w-5" />
                </span>
                <h3 className="mt-4 font-display text-lg font-bold text-ink">{f.title}</h3>
                <p className="mt-2 text-sm leading-6 text-muted">{f.body}</p>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* ------------------------------------------------------------ Final call to action */}
      <section className="py-16 sm:py-20">
        <div className="container-page">
          <div className="relative overflow-hidden rounded-[2rem] bg-navy-700 px-6 py-12 text-center text-white sm:rounded-[2.5rem] sm:px-16 sm:py-14">
            <div className="pointer-events-none absolute -left-20 -top-20 h-64 w-64 rounded-full bg-brand-500/30 blur-3xl" />
            <div className="pointer-events-none absolute -bottom-24 -right-16 h-64 w-64 rounded-full bg-gold-400/20 blur-3xl" />
            <div className="relative mx-auto max-w-2xl">
              <div className="mb-5 flex justify-center"><AvatarGroup size={48} /></div>
              <h2 className="font-display text-3xl font-extrabold sm:text-4xl">Ready to light up your learning?</h2>
              <p className="mt-4 text-base leading-7 text-white/70">
                Create a free account and start with a course that fits your goals. Your first lesson is waiting.
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

      <Footer />
    </div>
  );
}
