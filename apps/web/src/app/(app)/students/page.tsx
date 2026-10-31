"use client";

/**
 * Teacher/admin: roster of students enrolled in YOUR courses (admins: everyone),
 * sorted by risk so those who need help come first. Mobile = cards, desktop = table.
 */
import Link from "next/link";
import { useEffect, useState } from "react";
import { ChevronRight, Search, Users } from "lucide-react";

import Leaderboard from "@/components/teacher/Leaderboard";
import RiskBadge from "@/components/teacher/RiskBadge";
import { Avatar, Card, EmptyState, Input, ProgressBar, Skeleton } from "@/components/ui";
import { api } from "@/lib/api";
import { useRequireRole } from "@/lib/useRequireRole";
import { formatDate } from "@/lib/utils";
import type { RosterStudent } from "@/types";

export default function StudentsPage() {
  const ok = useRequireRole(["teacher", "admin"]);
  const [students, setStudents] = useState<RosterStudent[] | null>(null);
  const [q, setQ] = useState("");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!ok) return;
    const t = setTimeout(() => {
      api
        .get<{ students: RosterStudent[] }>(`/teacher/students?q=${encodeURIComponent(q)}`)
        .then((d) => setStudents(d.students))
        .catch((e) => setError(e instanceof Error ? e.message : "Could not load students."));
    }, 250); // debounce typing
    return () => clearTimeout(t);
  }, [q, ok]);

  if (!ok) return null;

  return (
    <div className="space-y-6">
      <div>
        <p className="text-sm font-semibold text-brand-600">Teacher workspace</p>
        <h1 className="mt-1 font-display text-3xl font-extrabold tracking-tight text-ink">Your students</h1>
        <p className="mt-1 text-sm text-muted">Learners enrolled in your courses, with those needing help listed first.</p>
      </div>

      <Leaderboard />

      <Input placeholder="Search by name or email…" icon={<Search className="h-4 w-4" />} value={q} onChange={(e) => setQ(e.target.value)} aria-label="Search students" />

      {error && <EmptyState icon={<Users className="h-5 w-5" />} title="Couldn't load students" description={error} />}
      {!students && !error && (
        <div className="space-y-3">{[0, 1, 2].map((i) => <Skeleton key={i} className="h-20 w-full" />)}</div>
      )}
      {students && students.length === 0 && (
        <EmptyState
          icon={<Users className="h-5 w-5" />}
          title={q ? "No matching students" : "No students yet"}
          description={q ? "Try a different name or email." : "Students appear here once they enrol in one of your courses. Share your course with them!"}
        />
      )}

      {students && students.length > 0 && (
        <>
          {/* Mobile: cards */}
          <div className="space-y-3 md:hidden">
            {students.map((s) => (
              <Link key={s.id} href={`/students/${s.id}`}>
                <Card className="flex items-center gap-3 p-4 active:bg-mist/60">
                  <Avatar name={s.name} />
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center justify-between gap-2">
                      <p className="truncate font-semibold text-ink">{s.name}</p>
                      <RiskBadge risk={s.risk} />
                    </div>
                    <p className="truncate text-xs text-muted">{s.courses.join(", ") || s.email}</p>
                    <div className="mt-2 flex items-center gap-3">
                      <ProgressBar value={s.completion} size="sm" className="flex-1" />
                      <span className="text-xs font-semibold text-muted">{s.completion}% · {s.avg_score ?? "—"}{s.avg_score !== null && "%"}</span>
                    </div>
                  </div>
                  <ChevronRight className="h-4 w-4 shrink-0 text-muted" />
                </Card>
              </Link>
            ))}
          </div>

          {/* Desktop: table */}
          <Card className="hidden overflow-hidden p-0 md:block">
            <table className="w-full text-left text-sm">
              <thead>
                <tr className="border-b border-line bg-mist/50 text-xs uppercase tracking-wide text-muted">
                  <th className="px-5 py-3 font-semibold">Student</th>
                  <th className="py-3 font-semibold">Courses</th>
                  <th className="py-3 font-semibold">Completion</th>
                  <th className="py-3 font-semibold">Avg score</th>
                  <th className="py-3 font-semibold">Last active</th>
                  <th className="py-3 pr-5 font-semibold">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-line/70">
                {students.map((s) => (
                  <tr key={s.id} className="hover:bg-mist/40">
                    <td className="px-5 py-3">
                      <Link href={`/students/${s.id}`} className="flex items-center gap-3">
                        <Avatar name={s.name} size="sm" />
                        <span>
                          <span className="block font-semibold text-ink">{s.name}</span>
                          <span className="block text-[11px] text-muted">{s.email}</span>
                        </span>
                      </Link>
                    </td>
                    <td className="max-w-[180px] truncate py-3 text-muted">{s.courses.join(", ")}</td>
                    <td className="w-40 py-3"><div className="flex items-center gap-2"><ProgressBar value={s.completion} size="sm" className="flex-1" /><span className="text-xs text-muted">{s.completion}%</span></div></td>
                    <td className="py-3 font-medium text-ink">{s.avg_score === null ? "—" : `${s.avg_score}%`}</td>
                    <td className="py-3 text-muted">{formatDate(s.last_active)}</td>
                    <td className="py-3 pr-5"><RiskBadge risk={s.risk} /></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </Card>
        </>
      )}
    </div>
  );
}
