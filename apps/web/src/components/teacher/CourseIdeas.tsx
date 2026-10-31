"use client";

/** Three course ideas that rotate every week (in-demand skills), each one tap away from a pre-filled new course. */
import { useRouter } from "next/navigation";
import { Lightbulb } from "lucide-react";

import { Card } from "@/components/ui";

interface Idea {
  title: string;
  subject: string;
  level: string;
  why: string;
}

const IDEAS: Idea[] = [
  { title: "Machine Learning & AI Fundamentals", subject: "Technology", level: "Beginner", why: "AI skills are among the most requested by employers." },
  { title: "Data Analysis with Excel and Python", subject: "Data", level: "Beginner", why: "Every field now needs people who can read data." },
  { title: "Introduction to Python Programming", subject: "Technology", level: "Beginner", why: "The most popular first language for new coders." },
  { title: "Using Generative AI Responsibly at Work", subject: "Technology", level: "Beginner", why: "Practical prompts, limits and ethics for everyday tasks." },
  { title: "Data Visualisation and Storytelling", subject: "Data", level: "Intermediate", why: "Turn spreadsheets into charts people understand." },
  { title: "Cybersecurity Basics", subject: "Technology", level: "Beginner", why: "Keeping accounts, phones and small businesses safe." },
  { title: "Digital Marketing Essentials", subject: "Business", level: "Beginner", why: "Reach customers through social media and search." },
  { title: "Web Development: HTML, CSS and JavaScript", subject: "Technology", level: "Beginner", why: "Learners can build a real site by the end." },
  { title: "Financial Literacy and Budgeting", subject: "Life skills", level: "Beginner", why: "Useful to every student, whatever they study next." },
  { title: "Project Management Fundamentals", subject: "Business", level: "Intermediate", why: "Planning, teamwork and delivering on time." },
  { title: "SQL and Databases for Beginners", subject: "Data", level: "Beginner", why: "The skill behind most data jobs." },
  { title: "Entrepreneurship: From Idea to First Customer", subject: "Business", level: "Beginner", why: "Great for students who want to start something." },
  { title: "Communication and Public Speaking", subject: "Life skills", level: "Beginner", why: "Confidence for interviews and presentations." },
];

/** Whole weeks since 1 Jan 1970 (Thursday), so the picks change once a week for everyone. */
function weekNumber(d = new Date()) {
  return Math.floor(d.getTime() / (7 * 24 * 3600 * 1000));
}

export default function CourseIdeas() {
  const router = useRouter();
  const start = (weekNumber() * 3) % IDEAS.length;
  const picks = [0, 1, 2].map((i) => IDEAS[(start + i) % IDEAS.length]);

  function create(i: Idea) {
    const q = new URLSearchParams({ new: "1", title: i.title, subject: i.subject, level: i.level, desc: i.why });
    router.push(`/courses?${q.toString()}`);
  }

  return (
    <Card className="p-5 sm:p-6">
      <p className="flex items-center gap-2 font-display text-lg font-bold text-ink"><Lightbulb className="h-5 w-5 text-gold-500" /> Course ideas this week</p>
      <p className="mt-0.5 text-sm text-muted">In-demand skills students are looking for. New ideas every week.</p>
      <ul className="mt-4 grid gap-3 md:grid-cols-3">
        {picks.map((i) => (
          <li key={i.title} className="flex flex-col rounded-2xl border border-line p-4">
            <p className="text-[11px] font-semibold uppercase tracking-wide text-brand-600">{i.subject} · {i.level}</p>
            <p className="mt-1 font-semibold text-ink">{i.title}</p>
            <p className="mt-1 flex-1 text-sm text-muted">{i.why}</p>
            <button onClick={() => create(i)} className="mt-3 min-h-[44px] rounded-xl bg-brand-50 px-4 text-sm font-semibold text-brand-700 hover:bg-brand-100">
              Create this course
            </button>
          </li>
        ))}
      </ul>
    </Card>
  );
}
