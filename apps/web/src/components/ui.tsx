/**
 * Small, reusable UI primitives.
 * Everything visual in the app is composed from these so styling stays
 * consistent with the Figma design (rounded cards, navy text, blue CTAs).
 */
import Image from "next/image";
import Link from "next/link";
import { forwardRef } from "react";
import { Loader2, Sparkles } from "lucide-react";

import { cn, initials } from "@/lib/utils";

/* ------------------------------------------------------------------ Button */
type ButtonVariant = "primary" | "secondary" | "ghost" | "gold" | "danger";
type ButtonSize = "sm" | "md" | "lg";

const variants: Record<ButtonVariant, string> = {
  primary:
    "bg-brand-500 text-white hover:bg-brand-600 active:bg-brand-700 shadow-[0_8px_20px_-8px_rgba(47,107,255,0.7)]",
  secondary: "bg-white text-ink border border-line hover:bg-mist",
  ghost: "bg-transparent text-navy-700 hover:bg-navy-50",
  gold: "bg-gold-400 text-navy-900 hover:bg-gold-500",
  danger: "bg-rose-500 text-white hover:bg-rose-600",
};

const sizes: Record<ButtonSize, string> = {
  sm: "h-9 px-3.5 text-sm rounded-xl",
  md: "h-11 px-5 text-sm rounded-2xl",
  lg: "h-12 px-6 text-[15px] rounded-2xl",
};

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  size?: ButtonSize;
  loading?: boolean;
  fullWidth?: boolean;
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(function Button(
  { className, variant = "primary", size = "md", loading, fullWidth, children, disabled, ...props },
  ref
) {
  return (
    <button
      ref={ref}
      disabled={disabled || loading}
      className={cn(
        "inline-flex items-center justify-center gap-2 font-semibold transition focus-visible:outline-none focus-visible:ring-4 focus-visible:ring-brand-500/20 disabled:cursor-not-allowed disabled:opacity-60",
        variants[variant],
        sizes[size],
        fullWidth && "w-full",
        className
      )}
      {...props}
    >
      {loading && <Loader2 className="h-4 w-4 animate-spin" />}
      {children}
    </button>
  );
});

/** Link styled as a button (for navigation CTAs). */
export function ButtonLink({
  href,
  variant = "primary",
  size = "md",
  className,
  children,
}: {
  href: string;
  variant?: ButtonVariant;
  size?: ButtonSize;
  className?: string;
  children: React.ReactNode;
}) {
  return (
    <Link
      href={href}
      className={cn(
        "inline-flex items-center justify-center gap-2 font-semibold transition focus-visible:outline-none focus-visible:ring-4 focus-visible:ring-brand-500/20",
        variants[variant],
        sizes[size],
        className
      )}
    >
      {children}
    </Link>
  );
}

/* ------------------------------------------------------------------- Input */
interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  hint?: string;
  error?: string;
  icon?: React.ReactNode;
}

export const Input = forwardRef<HTMLInputElement, InputProps>(function Input(
  { label, hint, error, icon, className, id, ...props },
  ref
) {
  const inputId = id ?? props.name;
  return (
    <div>
      {label && (
        <label htmlFor={inputId} className="label">
          {label}
        </label>
      )}
      <div className="relative">
        {icon && (
          <span className="pointer-events-none absolute left-4 top-1/2 -translate-y-1/2 text-muted">
            {icon}
          </span>
        )}
        <input
          ref={ref}
          id={inputId}
          className={cn("input-base", icon && "pl-11", error && "border-rose-400", className)}
          {...props}
        />
      </div>
      {error ? (
        <p className="mt-1.5 text-xs font-medium text-rose-600">{error}</p>
      ) : hint ? (
        <p className="mt-1.5 text-xs text-muted">{hint}</p>
      ) : null}
    </div>
  );
});

export const Select = forwardRef<HTMLSelectElement, React.SelectHTMLAttributes<HTMLSelectElement> & { label?: string }>(
  function Select({ label, className, id, children, ...props }, ref) {
    return (
      <div>
        {label && <label className="label">{label}</label>}
        <select ref={ref} id={id} className={cn("input-base appearance-none", className)} {...props}>
          {children}
        </select>
      </div>
    );
  }
);

/* -------------------------------------------------------------------- Card */
export function Card({
  className,
  children,
  as: Tag = "div",
}: {
  className?: string;
  children: React.ReactNode;
  as?: React.ElementType;
}) {
  return <Tag className={cn("card", className)}>{children}</Tag>;
}

export function CardHeader({
  title,
  subtitle,
  action,
  className,
}: {
  title: string;
  subtitle?: string;
  action?: React.ReactNode;
  className?: string;
}) {
  return (
    <div className={cn("flex items-start justify-between gap-4", className)}>
      <div>
        <h2 className="font-display text-lg font-bold text-ink">{title}</h2>
        {subtitle && <p className="mt-0.5 text-sm text-muted">{subtitle}</p>}
      </div>
      {action}
    </div>
  );
}

/* ------------------------------------------------------------------- Badge */
export function Badge({
  children,
  tone = "neutral",
  className,
}: {
  children: React.ReactNode;
  tone?: "neutral" | "blue" | "green" | "amber" | "rose" | "navy";
  className?: string;
}) {
  const tones = {
    neutral: "bg-mist text-muted",
    blue: "bg-brand-50 text-brand-700",
    green: "bg-emerald-50 text-emerald-700",
    amber: "bg-amber-50 text-amber-700",
    rose: "bg-rose-50 text-rose-700",
    navy: "bg-navy-50 text-navy-700",
  };
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 rounded-full px-2.5 py-1 text-xs font-semibold",
        tones[tone],
        className
      )}
    >
      {children}
    </span>
  );
}

/* ------------------------------------------------------------- ProgressBar */
export function ProgressBar({
  value,
  className,
  barClassName,
  size = "md",
}: {
  value: number;
  className?: string;
  barClassName?: string;
  size?: "sm" | "md" | "lg";
}) {
  const heights = { sm: "h-1.5", md: "h-2.5", lg: "h-3.5" };
  return (
    <div className={cn("w-full overflow-hidden rounded-full bg-navy-50", heights[size], className)}>
      <div
        className={cn("h-full rounded-full bg-brand-500 transition-all duration-700", barClassName)}
        style={{ width: `${Math.min(100, Math.max(0, value))}%` }}
      />
    </div>
  );
}

/* ------------------------------------------------------------ ProgressRing */
export function ProgressRing({
  value,
  size = 132,
  stroke = 12,
  label,
  sublabel,
  className,
}: {
  value: number;
  size?: number;
  stroke?: number;
  label?: string;
  sublabel?: string;
  className?: string;
}) {
  const radius = (size - stroke) / 2;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (Math.min(100, Math.max(0, value)) / 100) * circumference;
  return (
    <div className={cn("relative inline-flex items-center justify-center", className)} style={{ width: size, height: size }}>
      <svg width={size} height={size} className="-rotate-90">
        <circle cx={size / 2} cy={size / 2} r={radius} fill="none" stroke="#E4E9F5" strokeWidth={stroke} />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="url(#ringGradient)"
          strokeWidth={stroke}
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          className="transition-all duration-1000"
        />
        <defs>
          <linearGradient id="ringGradient" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0%" stopColor="#2F6BFF" />
            <stop offset="100%" stopColor="#7AA2FF" />
          </linearGradient>
        </defs>
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="font-display text-2xl font-extrabold text-ink">{label ?? `${value}%`}</span>
        {sublabel && <span className="text-[11px] font-medium text-muted">{sublabel}</span>}
      </div>
    </div>
  );
}

/* ------------------------------------------------------------------ Avatar */
export function Avatar({
  name,
  size = "md",
  className,
}: {
  name: string;
  size?: "sm" | "md" | "lg";
  className?: string;
}) {
  const sizes = { sm: "h-8 w-8 text-xs", md: "h-10 w-10 text-sm", lg: "h-14 w-14 text-lg" };
  return (
    <span
      className={cn(
        "inline-flex shrink-0 items-center justify-center rounded-full bg-navy-700 font-bold text-white",
        sizes[size],
        className
      )}
    >
      {initials(name)}
    </span>
  );
}

/* -------------------------------------------------------------- EmptyState */
export function EmptyState({
  icon,
  title,
  description,
  action,
}: {
  icon?: React.ReactNode;
  title: string;
  description?: string;
  action?: React.ReactNode;
}) {
  return (
    <div className="flex flex-col items-center justify-center rounded-3xl border border-dashed border-line bg-white/60 px-6 py-14 text-center">
      <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-2xl bg-brand-50 text-brand-600">
        {icon ?? <Sparkles className="h-5 w-5" />}
      </div>
      <h3 className="font-display text-base font-bold text-ink">{title}</h3>
      {description && <p className="mt-1 max-w-sm text-sm text-muted">{description}</p>}
      {action && <div className="mt-5">{action}</div>}
    </div>
  );
}

/* ---------------------------------------------------------------- Skeleton */
export function Skeleton({ className }: { className?: string }) {
  return <div className={cn("animate-pulse rounded-2xl bg-navy-50", className)} />;
}

export function PageLoader({ label = "Loading" }: { label?: string }) {
  return (
    <div className="flex min-h-[40vh] flex-col items-center justify-center gap-3 text-muted">
      <Loader2 className="h-6 w-6 animate-spin text-brand-500" />
      <p className="text-sm font-medium">{label}…</p>
    </div>
  );
}

/* -------------------------------------------------------------------- Logo */
/**
 * Brand logo: the real LightEd mark (bulb + graduation cap) from /public/logo-mark.png
 * next to a live-text wordmark. On dark surfaces (`variant="light"`) the mark sits on a
 * white tile so the navy cap stays readable.
 */
export function Logo({
  variant = "dark",
  className,
  showWordmark = true,
  size = 40,
}: {
  variant?: "dark" | "light";
  className?: string;
  showWordmark?: boolean;
  size?: number;
}) {
  return (
    <span className={cn("inline-flex items-center gap-2.5", className)}>
      <span
        className={cn(
          "flex shrink-0 items-center justify-center",
          variant === "light" && "rounded-xl bg-white p-1 shadow-sm"
        )}
        style={{ width: size, height: size }}
      >
        <Image src="/logo-mark.png" alt="LightEd logo" width={size} height={size} unoptimized priority className="h-full w-full object-contain" />
      </span>
      {showWordmark && (
        <span
          className={cn(
            "font-display text-xl font-extrabold tracking-tight",
            variant === "light" ? "text-white" : "text-navy-700"
          )}
        >
          Light<span className={variant === "light" ? "text-brand-300" : "text-brand-500"}>Ed</span>
        </span>
      )}
    </span>
  );
}
