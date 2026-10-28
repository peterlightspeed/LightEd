"use client";

/**
 * Authenticated application shell: fixed sidebar on desktop, slide-over on
 * mobile, plus a top bar with the signed-in user. Redirects to /login when no
 * session exists (client-side guard — fine for the MVP).
 */
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import {
  BarChart3,
  CalendarDays,
  Users,
  BookOpen,
  ChevronDown,
  GraduationCap,
  HelpCircle,
  LifeBuoy,
  LayoutDashboard,
  LogOut,
  Menu,
  Search,
  ShieldCheck,
  Sparkles,
  X,
} from "lucide-react";

import NotificationBell from "@/components/NotificationBell";
import ThemeToggle from "@/components/ThemeToggle";
import ProductTour from "@/components/tour/ProductTour";
import { getTourSteps } from "@/components/tour/tourSteps";
import { Avatar, Badge, Logo, PageLoader } from "@/components/ui";
import { SUPPORT_EMAIL, SUPPORT_PHONE_DISPLAY, SUPPORT_PHONE_TEL } from "@/lib/site";
import { useAuth } from "@/lib/auth-context";
import { homeForRole } from "@/lib/auth";
import { cn } from "@/lib/utils";
import type { Role } from "@/types";

interface NavItem {
  href: string;
  label: string;
  icon: React.ElementType;
  roles: Role[];
}

const NAV: NavItem[] = [
  { href: "/dashboard", label: "Overview", icon: LayoutDashboard, roles: ["student"] },
  { href: "/dashboard/teacher", label: "Overview", icon: LayoutDashboard, roles: ["teacher"] },
  { href: "/dashboard/admin", label: "Overview", icon: ShieldCheck, roles: ["admin"] },
  { href: "/courses", label: "Courses", icon: BookOpen, roles: ["student", "teacher", "admin"] },
  { href: "/students", label: "Students", icon: Users, roles: ["teacher", "admin"] },
  { href: "/tutor", label: "AI Tutor", icon: Sparkles, roles: ["student", "teacher"] },
  { href: "/planner", label: "Planner", icon: CalendarDays, roles: ["student"] },
  { href: "/progress", label: "Progress", icon: BarChart3, roles: ["student"] },
];

export default function AppShell({ children }: { children: React.ReactNode }) {
  const { user, loading, logout } = useAuth();
  const pathname = usePathname();
  const router = useRouter();
  const [mobileOpen, setMobileOpen] = useState(false);
  const [menuOpen, setMenuOpen] = useState(false);
  const [tourOpen, setTourOpen] = useState(false);

  useEffect(() => {
    if (!loading && !user) router.replace("/login");
  }, [loading, user, router]);

  // First visit: auto-start the tour once per user (remembered in localStorage).
  const tourKey = user ? `lighted_tour_v1_${user.id}` : null;
  useEffect(() => {
    if (!tourKey) return;
    try {
      if (!localStorage.getItem(tourKey)) {
        const t = setTimeout(() => setTourOpen(true), 900);
        return () => clearTimeout(t);
      }
    } catch {
      /* storage blocked: skip the auto tour */
    }
  }, [tourKey]);

  function closeTour() {
    setTourOpen(false);
    try {
      if (tourKey) localStorage.setItem(tourKey, "done");
    } catch {
      /* ignore */
    }
  }

  // Close overlays whenever the route changes.
  useEffect(() => {
    setMobileOpen(false);
    setMenuOpen(false);
  }, [pathname]);

  if (loading || !user) return <PageLoader label="Preparing your workspace" />;

  const items = NAV.filter((item) => item.roles.includes(user.role));
  const roleLabel = user.role === "teacher" ? "Teacher" : user.role === "admin" ? "Admin" : "Student";

  const sidebar = (
    <div className="flex h-full flex-col bg-navy-700 px-4 py-6 text-white">
      <div className="flex items-center justify-between px-2">
        <Link href="/">
          <Logo variant="light" />
        </Link>
        <button className="rounded-lg p-1.5 text-white/70 hover:bg-white/10 lg:hidden" onClick={() => setMobileOpen(false)}>
          <X className="h-5 w-5" />
        </button>
      </div>

      <div className="mt-8 rounded-2xl bg-white/10 p-4">
        <div className="flex items-center gap-3">
          <Avatar name={user.full_name} size="sm" className="bg-gold-400 text-navy-900" />
          <div className="min-w-0">
            <p className="truncate text-sm font-semibold">{user.full_name}</p>
            <p className="text-[11px] text-white/60">{roleLabel} account</p>
          </div>
        </div>
      </div>

      <nav className="mt-6 flex-1 space-y-1" data-tour="nav">
        <p className="px-3 pb-2 text-[10px] font-bold uppercase tracking-[0.2em] text-white/40">Menu</p>
        {items.map((item) => {
          const active = pathname === item.href;
          const Icon = item.icon;
          return (
            <Link
              key={`${item.href}-${item.label}`}
              href={item.href}
              data-tour={item.label === "Overview" ? "nav-overview" : `nav-${item.label.toLowerCase()}`}
              className={cn(
                "flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition",
                active ? "bg-white text-navy-700 shadow-sm" : "text-white/70 hover:bg-white/10 hover:text-white"
              )}
            >
              <Icon className="h-[18px] w-[18px]" />
              {item.label}
            </Link>
          );
        })}
      </nav>

      <div className="mt-6 rounded-2xl bg-gradient-to-br from-brand-500 to-brand-700 p-4" data-tour="ai-tutor">
        <div className="flex items-center gap-2 text-gold-300">
          <Sparkles className="h-4 w-4" />
          <span className="text-xs font-bold uppercase tracking-wide">AI Tutor</span>
        </div>
        <p className="mt-2 text-xs leading-5 text-white/80">
          Stuck on a topic? Ask the tutor for a step-by-step explanation.
        </p>
        <Link
          href="/tutor"
          className="mt-3 inline-flex min-h-[40px] items-center rounded-lg bg-white/15 px-3 py-1.5 text-xs font-semibold text-white hover:bg-white/25"
        >
          Ask a question
        </Link>
      </div>

      <button
        onClick={logout}
        className="mt-4 flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium text-white/60 transition hover:bg-white/10 hover:text-white"
      >
        <LogOut className="h-[18px] w-[18px]" />
        Log out
      </button>
    </div>
  );

  return (
    <div className="min-h-screen bg-mist">
      {/* Desktop sidebar */}
      <aside className="fixed inset-y-0 left-0 z-30 hidden w-64 lg:block">{sidebar}</aside>

      {/* Mobile drawer */}
      {mobileOpen && (
        <div className="fixed inset-0 z-50 lg:hidden">
          <div className="absolute inset-0 bg-navy-900/50 backdrop-blur-sm" onClick={() => setMobileOpen(false)} />
          <div className="absolute inset-y-0 left-0 w-72">{sidebar}</div>
        </div>
      )}

      <div className="lg:pl-64">
        {/* Top bar */}
        <header className="sticky top-0 z-20 border-b border-line bg-white/85 backdrop-blur-xl">
          <div className="flex h-16 items-center gap-3 px-4 sm:px-6 lg:px-8">
            <button className="flex h-11 w-11 items-center justify-center rounded-xl text-ink hover:bg-mist lg:hidden" onClick={() => setMobileOpen(true)} data-tour="menu-btn" aria-label="Open menu">
              <Menu className="h-5 w-5" />
            </button>

            <div data-tour="search" className="hidden flex-1 items-center gap-2 rounded-xl border border-line bg-mist/60 px-3 py-2 text-sm text-muted sm:flex sm:max-w-sm">
              <Search className="h-4 w-4" />
              <input
                placeholder="Search courses, lessons…"
                className="w-full bg-transparent text-sm outline-none placeholder:text-muted/70"
                onKeyDown={(e) => {
                  if (e.key === "Enter") router.push("/courses");
                }}
              />
            </div>

            <div className="ml-auto flex items-center gap-2 sm:gap-3">
              <Badge tone="blue" className="hidden sm:inline-flex">
                <GraduationCap className="h-3.5 w-3.5" /> {roleLabel}
              </Badge>
              <ThemeToggle />
              <NotificationBell />
              <button
                onClick={() => setTourOpen(true)}
                className="hidden h-11 w-11 items-center justify-center rounded-xl text-muted hover:bg-mist hover:text-ink sm:flex"
                aria-label="Take a tour"
                title="Take a tour"
              >
                <HelpCircle className="h-[18px] w-[18px]" />
              </button>
              <div className="relative" data-tour="user-menu">
                <button
                  onClick={() => setMenuOpen((v) => !v)}
                  className="flex items-center gap-2 rounded-xl p-1 pr-2 hover:bg-mist"
                >
                  <Avatar name={user.full_name} size="sm" />
                  <span className="hidden text-sm font-semibold text-ink sm:block">{user.full_name.split(" ")[0]}</span>
                  <ChevronDown className="h-4 w-4 text-muted" />
                </button>
                {menuOpen && (
                  <div className="absolute right-0 mt-2 w-56 rounded-2xl border border-line bg-white p-2 shadow-float">
                    <div className="px-3 py-2">
                      <p className="truncate text-sm font-semibold">{user.full_name}</p>
                      <p className="truncate text-xs text-muted">{user.email}</p>
                    </div>
                    <Link
                      href={homeForRole(user.role)}
                      className="flex items-center gap-2 rounded-xl px-3 py-2 text-sm text-muted hover:bg-mist hover:text-ink"
                    >
                      <LayoutDashboard className="h-4 w-4" /> Dashboard
                    </Link>
                    <button
                      onClick={() => {
                        setMenuOpen(false);
                        setTourOpen(true);
                      }}
                      className="flex w-full items-center gap-2 rounded-xl px-3 py-2 text-sm text-muted hover:bg-mist hover:text-ink"
                    >
                      <HelpCircle className="h-4 w-4" /> Take the tour
                    </button>
                    <div className="my-1 border-t border-line px-3 pb-1 pt-2">
                      <p className="flex items-center gap-1.5 text-[10px] font-bold uppercase tracking-wider text-muted">
                        <LifeBuoy className="h-3 w-3" /> Support
                      </p>
                      <a href={`mailto:${SUPPORT_EMAIL}`} className="mt-1 block truncate text-xs text-brand-600 hover:underline">
                        {SUPPORT_EMAIL}
                      </a>
                      <a href={`tel:${SUPPORT_PHONE_TEL}`} className="block text-xs text-brand-600 hover:underline">
                        {SUPPORT_PHONE_DISPLAY}
                      </a>
                    </div>
                    <button
                      onClick={logout}
                      className="flex w-full items-center gap-2 rounded-xl px-3 py-2 text-sm text-rose-600 hover:bg-rose-50"
                    >
                      <LogOut className="h-4 w-4" /> Log out
                    </button>
                  </div>
                )}
              </div>
            </div>
          </div>
        </header>

        <main className="px-4 py-6 pb-28 sm:px-6 lg:px-8 lg:py-8 lg:pb-8">{children}</main>
      </div>

      {/* Mobile bottom tab bar: thumb-friendly primary navigation (hidden on desktop). */}
      <nav
        aria-label="Primary"
        className="fixed inset-x-0 bottom-0 z-30 border-t border-line bg-white/95 backdrop-blur lg:hidden"
        style={{ paddingBottom: "env(safe-area-inset-bottom)" }}
      >
        <ul className="mx-auto flex max-w-xl">
          {items.slice(0, 5).map((item) => {
            const active = pathname === item.href || (item.href !== "/dashboard" && !item.href.startsWith("/dashboard") && pathname.startsWith(item.href));
            const Icon = item.icon;
            return (
              <li key={`${item.href}-b`} className="flex-1">
                <Link
                  href={item.href}
                  data-tour={item.label === "Overview" ? "nav-overview" : `nav-${item.label.toLowerCase()}`}
                  className={`flex min-h-[58px] flex-col items-center justify-center gap-0.5 text-[11px] font-semibold ${active ? "text-brand-600" : "text-muted"}`}
                >
                  <Icon className="h-5 w-5" />
                  {item.label === "Overview" ? "Home" : item.label === "AI Tutor" ? "Tutor" : item.label}
                </Link>
              </li>
            );
          })}
        </ul>
      </nav>

      <ProductTour open={tourOpen} onClose={closeTour} steps={getTourSteps(user.role, user.full_name.split(" ")[0])} />
    </div>
  );
}
