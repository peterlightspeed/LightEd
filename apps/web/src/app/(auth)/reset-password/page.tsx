"use client";

/** Landing page of the emailed reset link: /reset-password?token=... */
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { Suspense, useState } from "react";

import { Button, Input } from "@/components/ui";
import { api } from "@/lib/api";

function ResetForm() {
  const token = useSearchParams().get("token") ?? "";
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [busy, setBusy] = useState(false);
  const [done, setDone] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    if (password !== confirm) return setError("Passwords don't match.");
    setBusy(true);
    try {
      await api.post("/auth/reset-password", { token, password }, false);
      setDone(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not reset your password.");
    } finally {
      setBusy(false);
    }
  }

  if (done)
    return (
      <div>
        <h1 className="font-display text-3xl font-extrabold text-ink">Password updated ✓</h1>
        <p className="mt-2 text-sm text-muted">You can now log in with your new password.</p>
        <Link href="/login" className="mt-6 inline-flex min-h-[48px] w-full items-center justify-center rounded-xl bg-brand-600 px-4 text-sm font-semibold text-white">
          Go to login
        </Link>
      </div>
    );

  return (
    <div>
      <h1 className="font-display text-3xl font-extrabold text-ink">Choose a new password</h1>
      <p className="mt-1 text-sm text-muted">At least 8 characters.</p>
      {!token && <p className="mt-4 rounded-xl bg-rose-50 px-4 py-3 text-sm font-medium text-rose-700">This link is missing its token. Open the link from your email again.</p>}
      <form onSubmit={submit} className="mt-6 space-y-4">
        <Input label="New password" name="password" type="password" required minLength={8} value={password} onChange={(e) => setPassword(e.target.value)} autoComplete="new-password" />
        <Input label="Confirm password" name="confirm" type="password" required minLength={8} value={confirm} onChange={(e) => setConfirm(e.target.value)} autoComplete="new-password" />
        {error && <p className="rounded-xl bg-rose-50 px-4 py-2.5 text-sm font-medium text-rose-700">{error}</p>}
        <Button type="submit" fullWidth size="lg" loading={busy} disabled={!token}>Update password</Button>
      </form>
      <p className="mt-6 text-center text-sm text-muted">
        Link expired? <Link href="/forgot-password" className="font-semibold text-brand-600">Request a new one</Link>
      </p>
    </div>
  );
}

export default function ResetPasswordPage() {
  return (
    <Suspense fallback={null}>
      <ResetForm />
    </Suspense>
  );
}
