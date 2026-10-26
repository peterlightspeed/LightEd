"use client";

/**
 * Login page.
 *
 * Email + password against the FastAPI /auth/login endpoint. On success we
 * route the user to the dashboard that matches their role.
 */
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useState } from "react";
import { Eye, EyeOff, Lock, Mail } from "lucide-react";

import { Button, Input } from "@/components/ui";
import { useAuth } from "@/lib/auth-context";
import { homeForRole } from "@/lib/auth";

function LoginForm() {
  const router = useRouter();
  const params = useSearchParams();
  const { login } = useAuth();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function onSubmit(event: React.FormEvent) {
    event.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const user = await login(email.trim(), password);
      const next = params.get("next") ?? homeForRole(user.role);
      router.push(next);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not sign in. Please try again.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="w-full max-w-md">
      <h1 className="font-display text-3xl font-extrabold tracking-tight text-ink">Welcome back</h1>
      <p className="mt-2 text-sm text-muted">Sign in to pick up where you left off.</p>

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

        <div>
          <div className="mb-1.5 flex items-center justify-between">
            <label htmlFor="password" className="label mb-0">
              Password
            </label>
            <Link href="/forgot-password" className="text-xs font-semibold text-brand-600 hover:text-brand-700">
              Forgot password?
            </Link>
          </div>
          <div className="relative">
            <span className="pointer-events-none absolute left-4 top-1/2 -translate-y-1/2 text-muted">
              <Lock className="h-4 w-4" />
            </span>
            <input
              id="password"
              name="password"
              type={showPassword ? "text" : "password"}
              autoComplete="current-password"
              required
              placeholder="••••••••"
              className="input-base pl-11 pr-11"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
            <button
              type="button"
              onClick={() => setShowPassword((v) => !v)}
              className="absolute right-3 top-1/2 -translate-y-1/2 rounded-lg p-1.5 text-muted hover:text-ink"
              aria-label={showPassword ? "Hide password" : "Show password"}
            >
              {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
            </button>
          </div>
        </div>

        {error && (
          <div className="rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm font-medium text-rose-700">
            {error}
          </div>
        )}

        <Button type="submit" fullWidth size="lg" loading={loading}>
          Sign in
        </Button>
      </form>

      {/* Demo credentials — labelled clearly as an MVP convenience. */}
      <div className="mt-6 rounded-2xl border border-dashed border-line bg-mist/60 p-4">
        <p className="text-xs font-bold uppercase tracking-wider text-muted">Demo accounts</p>
        <div className="mt-2 space-y-1 text-xs text-muted">
          <p><span className="font-semibold text-ink">Student</span> student@lighted.dev</p>
          <p><span className="font-semibold text-ink">Teacher</span> teacher@lighted.dev</p>
          <p><span className="font-semibold text-ink">Admin</span> admin@lighted.dev</p>
          <p className="pt-1">Password for all: <span className="font-mono font-semibold text-ink">password123</span></p>
        </div>
      </div>

      <p className="mt-8 text-center text-sm text-muted">
        New to LightEd?{" "}
        <Link href="/register" className="font-semibold text-brand-600 hover:text-brand-700">
          Create an account
        </Link>
      </p>
    </div>
  );
}

/** useSearchParams() must sit inside a Suspense boundary for static export. */
export default function LoginPage() {
  return (
    <Suspense fallback={<div className="w-full max-w-md animate-pulse space-y-4"><div className="h-9 w-48 rounded-xl bg-navy-50" /><div className="h-12 rounded-2xl bg-navy-50" /><div className="h-12 rounded-2xl bg-navy-50" /></div>}>
      <LoginForm />
    </Suspense>
  );
}
