"use client";

/**
 * Forgot-password placeholder.
 *
 * The backend endpoint always returns 200 (no account enumeration), so this
 * screen simply confirms that a reset link would be sent. Wiring a real email
 * provider is listed in GUIDE.md as a post-MVP task.
 */
import Link from "next/link";
import { useState } from "react";
import { ArrowLeft, CheckCircle2, Mail } from "lucide-react";

import { Button, Input } from "@/components/ui";
import { api } from "@/lib/api";

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState("");
  const [sent, setSent] = useState(false);
  const [loading, setLoading] = useState(false);

  async function onSubmit(event: React.FormEvent) {
    event.preventDefault();
    setLoading(true);
    try {
      await api.post("/auth/forgot-password", { email: email.trim() }, false);
    } catch {
      // Intentionally ignored: we never reveal whether the email exists.
    } finally {
      setLoading(false);
      setSent(true);
    }
  }

  if (sent) {
    return (
      <div className="w-full max-w-md text-center">
        <span className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-emerald-50 text-emerald-600">
          <CheckCircle2 className="h-7 w-7" />
        </span>
        <h1 className="mt-5 font-display text-2xl font-extrabold text-ink">Check your inbox</h1>
        <p className="mt-2 text-sm text-muted">
          If an account exists for <span className="font-semibold text-ink">{email}</span>, we&apos;ve sent
          instructions to reset your password.
        </p>
        <Link
          href="/login"
          className="mt-8 inline-flex items-center gap-2 text-sm font-semibold text-brand-600 hover:text-brand-700"
        >
          <ArrowLeft className="h-4 w-4" />
          Back to sign in
        </Link>
      </div>
    );
  }

  return (
    <div className="w-full max-w-md">
      <h1 className="font-display text-3xl font-extrabold tracking-tight text-ink">Reset your password</h1>
      <p className="mt-2 text-sm text-muted">
        Enter the email you signed up with and we&apos;ll send you a reset link.
      </p>

      <form onSubmit={onSubmit} className="mt-8 space-y-5">
        <Input
          label="Email address"
          name="email"
          type="email"
          autoComplete="email"
          required
          placeholder="you@example.com"
          icon={<Mail className="h-4 w-4" />}
          value={email}
          onChange={(e) => setEmail(e.target.value)}
        />
        <Button type="submit" fullWidth size="lg" loading={loading}>
          Send reset link
        </Button>
      </form>

      <Link
        href="/login"
        className="mt-8 inline-flex items-center gap-2 text-sm font-semibold text-brand-600 hover:text-brand-700"
      >
        <ArrowLeft className="h-4 w-4" />
        Back to sign in
      </Link>
    </div>
  );
}
