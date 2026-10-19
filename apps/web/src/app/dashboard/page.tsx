"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import ProgressChart from "@/components/ProgressChart";
import QuizCard from "@/components/QuizCard";

export default function DashboardPage() {
  const [courses, setCourses] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api
      .get("/dashboard/student")
      .then(({ data }) => setCourses(data.courses ?? []))
      .catch(() => setCourses([]))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <p>Loading your dashboard…</p>;

  return (
    <div className="space-y-8">
      <h1 className="text-2xl font-bold">My Learning</h1>

      <section className="rounded-xl border border-slate-200 bg-white p-6">
        <h2 className="mb-4 text-lg font-semibold">Progress overview</h2>
        <ProgressChart />
      </section>

      <section className="grid gap-6 sm:grid-cols-2">
        {courses.map((c) => (
          <QuizCard key={c.id} course={c} />
        ))}
        {courses.length === 0 && (
          <p className="text-slate-500">No enrollments yet. Browse courses to get started.</p>
        )}
      </section>
    </div>
  );
}
