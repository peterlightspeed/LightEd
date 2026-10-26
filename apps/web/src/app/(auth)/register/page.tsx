"use client";

/**
 * Registration page with a two-step flow that mirrors the Figma screens:
 *   1. "Create your account"  -> name, email, password
 *   2. "Select your role"     -> student or teacher
 *
 * Admins are seeded, not self-registered (safer default for the MVP).
 */
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { ArrowLeft, ArrowRight, Check, Eye, EyeOff, GraduationCap, Lock, Mail, User, Users } from "lucide-react";

import GoogleButton from "@/components/auth/GoogleButton";
import { Button, Input } from "@/components/ui";
import { useSlowHint } from "@/lib/hooks";
import { useAuth } from "@/lib/auth-context";
import { homeForRole } from "@/lib/auth";
import { cn } from "@/lib/utils";

type Step = "details" | "role";

const roles = [
  {
    value: "student" as const,
    title: "I'm a student",
    description: "Follow courses, take quizzes, and track your own progress.",
    icon: GraduationCap,
  },
  {
    value: "teacher" as const,
    title: "I'm a teacher",
    description: "Publish courses and keep an eye on how your class is doing.",
    icon: Users,
  },
];

export default function RegisterPage() {
  const router = useRouter();
  const { register } = useAuth();

  const [step, setStep] = useState<Step>("details");
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [role, setRole] = useState<"student" | "teacher">("student");
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const slow = useSlowHint(loading);

  /** Validate the first step locally before advancing. */
  function goToRole(event: React.FormEvent) {
    event.preventDefault();
    setError(null);
    if (password.length < 6) {
      setError("Password must be at least 6 characters.");
      return;
    }
    setStep("role");
  }

  async function onSubmit() {
    setError(null);
    setLoading(true);
    try {
      const user = await register({
        full_name: fullName.trim(),
        email: email.trim(),
        password,
        role,
      });
      router.push(homeForRole(user.role));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not create your account.");
      setStep("details");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="w-full max-w-md">
      {/* Progress indicator for the two-step flow. */}
      <div className="mb-8 flex items-center gap-3">
        {(["details", "role"] as Step[]).map((value, index) => {
          const active = step === value;
          const done = value === "details" && step === "role";
          return (
            <div key={value} className="flex flex-1 items-center gap-3">
              <span
                className={cn(
                  "flex h-8 w-8 items-center justify-center rounded-full text-xs font-bold transition",
                  active || done ? "bg-brand-500 text-white" : "bg-mist text-muted"
                )}
              >
                {done ? <Check className="h-4 w-4" /> : index + 1}
              </span>
              <span className={cn("text-xs font-semibold", active || done ? "text-ink" : "text-muted")}>
                {value === "details" ? "Your details" : "Your role"}
              </span>
              {index === 0 && <span className="h-px flex-1 bg-line" />}
            </div>
          );
        })}
      </div>

      {step === "details" ? (
        <>
          <h1 className="font-display text-3xl font-extrabold tracking-tight text-ink">Create your account</h1>
          <p className="mt-2 text-sm text-muted">It takes less than a minute. No credit card needed.</p>

          <form onSubmit={goToRole} className="mt-8 space-y-5">
            <Input
              label="Full name"
              name="full_name"
              autoComplete="name"
              required
              placeholder="Sam Rivera"
              icon={<User className="h-4 w-4" />}
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
            />
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
              <label htmlFor="password" className="label">
                Password
              </label>
              <div className="relative">
                <span className="pointer-events-none absolute left-4 top-1/2 -translate-y-1/2 text-muted">
                  <Lock className="h-4 w-4" />
                </span>
                <input
                  id="password"
                  name="password"
                  type={showPassword ? "text" : "password"}
                  autoComplete="new-password"
                  required
                  minLength={6}
                  placeholder="At least 6 characters"
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

            <Button type="submit" fullWidth size="lg">
              Continue
              <ArrowRight className="h-4 w-4" />
            </Button>
          </form>
        </>
      ) : (
        <>
          <h1 className="font-display text-3xl font-extrabold tracking-tight text-ink">How will you use LightEd?</h1>
          <p className="mt-2 text-sm text-muted">This decides your dashboard. You can ask an admin to change it later.</p>

          <div className="mt-8 space-y-3">
            {roles.map((option) => {
              const Icon = option.icon;
              const selected = role === option.value;
              return (
                <button
                  key={option.value}
                  type="button"
                  onClick={() => setRole(option.value)}
                  className={cn(
                    "flex w-full items-start gap-4 rounded-2xl border p-4 text-left transition",
                    selected
                      ? "border-brand-500 bg-brand-50/60 ring-4 ring-brand-500/10"
                      : "border-line bg-white hover:border-brand-300"
                  )}
                >
                  <span
                    className={cn(
                      "flex h-11 w-11 shrink-0 items-center justify-center rounded-xl",
                      selected ? "bg-brand-500 text-white" : "bg-mist text-muted"
                    )}
                  >
                    <Icon className="h-5 w-5" />
                  </span>
                  <span className="flex-1">
                    <span className="block font-display text-base font-bold text-ink">{option.title}</span>
                    <span className="mt-0.5 block text-sm text-muted">{option.description}</span>
                  </span>
                  <span
                    className={cn(
                      "mt-1 flex h-5 w-5 items-center justify-center rounded-full border-2",
                      selected ? "border-brand-500 bg-brand-500 text-white" : "border-line"
                    )}
                  >
                    {selected && <Check className="h-3 w-3" />}
                  </span>
                </button>
              );
            })}
          </div>

          {error && (
            <div className="mt-4 rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm font-medium text-rose-700">
              {error}
            </div>
          )}

          <div className="mt-8 flex gap-3">
            <Button variant="secondary" size="lg" onClick={() => setStep("details")} disabled={loading}>
              <ArrowLeft className="h-4 w-4" />
              Back
            </Button>
            <Button fullWidth size="lg" loading={loading} onClick={onSubmit}>
              Create {role} account
            </Button>
          </div>
          {slow && (
            <p className="mt-3 text-center text-xs text-muted">
              Waking up the server (free hosting) — this can take up to a minute. Hang tight…
            </p>
          )}
          <GoogleButton role={role} label={`or sign up with Google as a ${role}`} />
        </>
      )}

      <p className="mt-8 text-center text-sm text-muted">
        Already have an account?{" "}
        <Link href="/login" className="font-semibold text-brand-600 hover:text-brand-700">
          Sign in
        </Link>
      </p>
    </div>
  );
}
