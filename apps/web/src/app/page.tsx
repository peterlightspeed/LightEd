import Link from "next/link";

const features = [
  { title: "AI Tutor", desc: "Ask questions, get answers grounded in your course material." },
  { title: "Personalized Paths", desc: "Recommendations that adapt to your strengths and gaps." },
  { title: "Auto Quizzes", desc: "Generate practice questions from any lesson instantly." },
  { title: "Progress Tracking", desc: "See mastery per topic and stay on track." },
  { title: "Teacher Dashboards", desc: "Class analytics and at-risk student alerts." },
  { title: "Secure Access", desc: "JWT auth with student, teacher, and admin roles." },
];

export default function HomePage() {
  return (
    <div>
      <section className="py-16 text-center">
        <h1 className="text-4xl font-bold tracking-tight sm:text-5xl">
          Learn smarter with <span className="text-brand-600">LightEd</span>
        </h1>
        <p className="mx-auto mt-4 max-w-2xl text-lg text-slate-600">
          An AI-powered personalized learning platform for students and teachers.
        </p>
        <div className="mt-8 flex justify-center gap-4">
          <Link
            href="/register"
            className="rounded-lg bg-brand-600 px-6 py-3 font-medium text-white hover:bg-brand-700"
          >
            Get Started
          </Link>
          <Link
            href="/login"
            className="rounded-lg border border-slate-300 px-6 py-3 font-medium hover:bg-white"
          >
            Log in
          </Link>
        </div>
      </section>

      <section className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
        {features.map((f) => (
          <div key={f.title} className="rounded-xl border border-slate-200 bg-white p-6">
            <h3 className="text-lg font-semibold">{f.title}</h3>
            <p className="mt-2 text-sm text-slate-600">{f.desc}</p>
          </div>
        ))}
      </section>
    </div>
  );
}
