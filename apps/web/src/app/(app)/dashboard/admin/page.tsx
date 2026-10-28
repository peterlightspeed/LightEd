"use client";

/**
 * Admin shell.
 *
 * A deliberately simple operations view: platform stats, a user table with
 * inline role changes, and a course list with a publish toggle. Enough to
 * demonstrate the admin role without building a full CMS.
 */
import { useEffect, useState } from "react";
import { BookOpen, GraduationCap, ShieldCheck, Users, UserCog } from "lucide-react";

import { Avatar, Badge, Card, CardHeader, EmptyState, Select, Skeleton } from "@/components/ui";
import { api } from "@/lib/api";
import type { AdminDashboard, AuditEntry, Role } from "@/types";

export default function AdminDashboardPage() {
  const [data, setData] = useState<AdminDashboard | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busyId, setBusyId] = useState<number | null>(null);

  async function load() {
    try {
      const fresh = await api.get<AdminDashboard>("/dashboard/admin");
      setData(fresh);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not load admin data.");
    }
  }

  useEffect(() => {
    load();
  }, []);

  /** Persist a role change, then refresh the table. */
  async function changeRole(userId: number, role: Role) {
    setBusyId(userId);
    try {
      await api.patch(`/admin/users/${userId}/role`, { role });
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not update the role.");
    } finally {
      setBusyId(null);
    }
  }

  /** Toggle a course between published and draft. */
  async function togglePublish(courseId: number, published: boolean) {
    setBusyId(courseId);
    try {
      await api.patch(`/admin/courses/${courseId}/publish`, { published: !published });
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not update the course.");
    } finally {
      setBusyId(null);
    }
  }

  if (error) {
    return <EmptyState icon={<ShieldCheck className="h-5 w-5" />} title="Admin data unavailable" description={error} />;
  }

  if (!data) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-24 w-full" />
        <div className="grid grid-cols-2 gap-3 sm:gap-4 lg:grid-cols-5">
          {Array.from({ length: 5 }).map((_, i) => (
            <Skeleton key={i} className="h-24" />
          ))}
        </div>
        <Skeleton className="h-80 w-full" />
      </div>
    );
  }

  const { stats, users, courses } = data;
  const statCards = [
    { label: "Users", value: stats.users, icon: Users },
    { label: "Students", value: stats.students, icon: GraduationCap },
    { label: "Teachers", value: stats.teachers, icon: UserCog },
    { label: "Courses", value: stats.courses, icon: BookOpen },
    { label: "Quiz attempts", value: stats.attempts, icon: ShieldCheck },
  ];

  return (
    <div className="space-y-7">
      <div>
        <p className="text-sm font-semibold text-brand-600">Platform administration</p>
        <h1 className="mt-1 font-display text-3xl font-extrabold tracking-tight text-ink">Admin overview</h1>
        <p className="mt-1 text-sm text-muted">Manage accounts, roles, and course visibility.</p>
      </div>

      <div className="grid grid-cols-2 gap-3 sm:gap-4 lg:grid-cols-5">
        {statCards.map((card) => {
          const Icon = card.icon;
          return (
            <Card key={card.label} className="p-5">
              <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-navy-50 text-navy-700">
                <Icon className="h-5 w-5" />
              </span>
              <p className="mt-3 font-display text-2xl font-extrabold text-ink">{card.value}</p>
              <p className="text-xs font-medium text-muted">{card.label}</p>
            </Card>
          );
        })}
      </div>

      <Card>
        <CardHeader title="Users" subtitle="Change a role to grant teacher or admin access." />
        {/* Phones: one card per user, role select stays usable. */}
        <div className="mt-4 divide-y divide-line/70 md:hidden">
          {users.map((user) => (
            <div key={user.id} className="py-3">
              <div className="flex items-center gap-3">
                <Avatar name={user.full_name} size="sm" />
                <div className="min-w-0 flex-1">
                  <p className="truncate font-semibold text-ink">{user.full_name}</p>
                  <p className="truncate text-xs text-muted">{user.email}</p>
                </div>
              </div>
              <Select
                value={user.role}
                disabled={busyId === user.id}
                onChange={(e) => changeRole(user.id, e.target.value as Role)}
                className="mt-2 w-full"
                aria-label={`Role for ${user.full_name}`}
              >
                <option value="student">Student</option>
                <option value="teacher">Teacher</option>
                <option value="admin">Admin</option>
              </Select>
            </div>
          ))}
        </div>
        <div className="mt-4 hidden overflow-x-auto md:block">
          <table className="w-full min-w-[640px] text-left text-sm">
            <thead>
              <tr className="border-b border-line text-xs uppercase tracking-wide text-muted">
                <th className="pb-3 font-semibold">Name</th>
                <th className="pb-3 font-semibold">Email</th>
                <th className="pb-3 font-semibold">Role</th>
                <th className="pb-3 font-semibold">Joined</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-line/70">
              {users.map((user) => (
                <tr key={user.id} className="hover:bg-mist/40">
                  <td className="py-3">
                    <div className="flex items-center gap-3">
                      <Avatar name={user.full_name} size="sm" />
                      <span className="font-semibold text-ink">{user.full_name}</span>
                    </div>
                  </td>
                  <td className="py-3 text-muted">{user.email}</td>
                  <td className="py-3">
                    <Select
                      value={user.role}
                      disabled={busyId === user.id}
                      onChange={(e) => changeRole(user.id, e.target.value as Role)}
                      className="h-9 w-36 py-1 text-xs"
                    >
                      <option value="student">Student</option>
                      <option value="teacher">Teacher</option>
                      <option value="admin">Admin</option>
                    </Select>
                  </td>
                  <td className="py-3 text-muted">
                    {user.created_at ? new Date(user.created_at).toLocaleDateString() : "—"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>

      <Card>
        <CardHeader title="Courses" subtitle="Publish or unpublish a course from the catalogue." />
        <div className="mt-4 space-y-3">
          {courses.map((course) => (
            <div
              key={course.id}
              className="flex flex-col justify-between gap-3 rounded-2xl border border-line/70 p-4 sm:flex-row sm:items-center"
            >
              <div>
                <p className="font-semibold text-ink">{course.title}</p>
                <p className="text-xs text-muted">{course.subject}</p>
              </div>
              <div className="flex items-center gap-3">
                <Badge tone={course.published ? "green" : "neutral"}>
                  {course.published ? "Published" : "Draft"}
                </Badge>
                <button
                  onClick={() => togglePublish(course.id, course.published)}
                  disabled={busyId === course.id}
                  className="rounded-xl border border-line px-3 py-1.5 text-xs font-semibold text-ink transition hover:bg-mist disabled:opacity-50"
                >
                  {course.published ? "Unpublish" : "Publish"}
                </button>
              </div>
            </div>
          ))}
        </div>
      </Card>
      <AuditCard />
    </div>
  );
}


/** Recent security/admin events (PDF FR-24): logins, failed logins, role changes, quiz publishing. */
function AuditCard() {
  const [rows, setRows] = useState<AuditEntry[] | null>(null);
  useEffect(() => {
    api.get<AuditEntry[]>("/admin/audit?limit=30").then(setRows).catch(() => setRows([]));
  }, []);
  return (
    <Card className="p-5 sm:p-6">
      <h2 className="font-display text-lg font-bold text-ink">Audit log</h2>
      <p className="text-sm text-muted">Latest security and admin activity.</p>
      <div className="mt-3 divide-y divide-line/70">
        {rows === null && <p className="py-3 text-sm text-muted">Loading…</p>}
        {rows?.length === 0 && <p className="py-3 text-sm text-muted">No events yet.</p>}
        {rows?.map((r) => (
          <div key={r.id} className="py-2.5 text-sm">
            <div className="flex flex-wrap items-center justify-between gap-x-3">
              <span className={`font-semibold ${r.action.includes("failed") ? "text-rose-600" : "text-ink"}`}>{r.action}</span>
              <span className="text-xs text-muted">{r.created_at ? new Date(r.created_at).toLocaleString() : ""}</span>
            </div>
            <p className="truncate text-xs text-muted">{r.actor || "anonymous"} {r.detail && `· ${r.detail}`} {r.ip && `· ${r.ip}`}</p>
          </div>
        ))}
      </div>
    </Card>
  );
}
