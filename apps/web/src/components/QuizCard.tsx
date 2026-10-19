import Link from "next/link";

export default function QuizCard({ course }: { course: any }) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-6">
      <h3 className="text-lg font-semibold">{course.title ?? "Untitled course"}</h3>
      <p className="mt-1 text-sm text-slate-600">{course.description ?? ""}</p>
      <div className="mt-4 flex gap-3">
        <Link
          href={`/courses/${course.id}`}
          className="rounded-lg bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700"
        >
          Continue
        </Link>
        <Link
          href={`/quiz/${course.id}`}
          className="rounded-lg border border-slate-300 px-4 py-2 text-sm font-medium hover:bg-slate-50"
        >
          Take quiz
        </Link>
      </div>
    </div>
  );
}
