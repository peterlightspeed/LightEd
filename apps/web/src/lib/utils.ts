import { clsx, type ClassValue } from "clsx";

/** Tailwind-friendly conditional class helper. */
export function cn(...inputs: ClassValue[]) {
  return clsx(inputs);
}

/** "Sam Rivera" -> "SR" */
export function initials(name: string) {
  return name
    .split(" ")
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase())
    .join("");
}

export function formatDate(value?: string | null) {
  if (!value) return "—";
  return new Date(value).toLocaleDateString(undefined, {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

/** Accent name -> gradient classes used on course cards. */
export const ACCENTS: Record<string, { bg: string; text: string; solid: string; soft: string }> = {
  blue: {
    bg: "from-brand-500 to-brand-700",
    text: "text-brand-700",
    solid: "bg-brand-500",
    soft: "bg-brand-50",
  },
  emerald: {
    bg: "from-emerald-400 to-emerald-600",
    text: "text-emerald-700",
    solid: "bg-emerald-500",
    soft: "bg-emerald-50",
  },
  amber: {
    bg: "from-amber-400 to-orange-500",
    text: "text-amber-700",
    solid: "bg-amber-500",
    soft: "bg-amber-50",
  },
  violet: {
    bg: "from-violet-500 to-purple-700",
    text: "text-violet-700",
    solid: "bg-violet-500",
    soft: "bg-violet-50",
  },
  rose: {
    bg: "from-rose-400 to-pink-600",
    text: "text-rose-700",
    solid: "bg-rose-500",
    soft: "bg-rose-50",
  },
};

export function accent(name?: string) {
  return ACCENTS[name ?? "blue"] ?? ACCENTS.blue;
}


/** "Good morning" / "Good afternoon" / "Good evening" from the device's local time. */
export function timeGreeting(date: Date = new Date()): string {
  const h = date.getHours();
  return h < 12 ? "Good morning" : h < 17 ? "Good afternoon" : "Good evening";
}

/** Shared demo logins (student@/teacher@/admin@lighted.dev) belong to everyone, so we never greet them by a name. */
export function isDemoAccount(email?: string | null): boolean {
  return !!email && email.toLowerCase().endsWith("@lighted.dev");
}

/** "Good evening, Amina" for real accounts; just "Good evening" for demo accounts. */
export function greetingFor(user?: { full_name?: string; email?: string } | null): string {
  const g = timeGreeting();
  if (!user?.full_name || isDemoAccount(user.email)) return g;
  return `${g}, ${user.full_name.trim().split(" ")[0]}`;
}
