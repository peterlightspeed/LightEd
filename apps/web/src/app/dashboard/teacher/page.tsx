"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import ProgressChart from "@/components/ProgressChart";

export default function TeacherDashboardPage() {
  const [analytics, setAnalytics] = useState<any | null>(null);

  useEffect(() => {
    api.get("/dashboard/teacher").then(({ data }) => setAnalytics(data)).catch(() => {});
  }, []);

  return (
    <div className="space-y-8">
      <h1 className="text-2xl font-bold">Teacher Dashboard</h1>

      <section className="grid gap-6 sm:grid-cols-3">
        <Stat label="Students" value={analytics?.student_count ?? "—"} />
        <Stat label="Avg. score" value={analytics?.avg_score ?? "—"} />
        <Stat label="At risk" value={analytics?.at_risk ?? "—"} />
      </section>

      <section className="rounded-xl border border-slate-200 bg-white p-6">
        <h2 className="mb-4 text-lg font-semibold">Class performance</h2>
        <ProgressChart />
      </section>
    </div>
  );
}

function Stat({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-6">
      <p className="text-sm text-slate-500">{label}</p>
      <p className="mt-1 text-3xl font-bold">{value}</p>
    </div>
  );
}
