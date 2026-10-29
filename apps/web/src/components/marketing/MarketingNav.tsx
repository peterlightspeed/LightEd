"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { Menu, X } from "lucide-react";

import { ButtonLink, Logo } from "@/components/ui";
import { useAuth } from "@/lib/auth-context";
import { homeForRole } from "@/lib/auth";


export default function MarketingNav() {
  const [open, setOpen] = useState(false);
  const [scrolled, setScrolled] = useState(false);
  const { user, loading } = useAuth();

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 8);
    window.addEventListener("scroll", onScroll);
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  return (
    <header
      className={`sticky top-0 z-40 transition ${
        scrolled ? "border-b border-line/80 bg-white/85 backdrop-blur-xl" : "bg-transparent"
      }`}
    >
      <div className="container-page flex h-20 items-center justify-between">
        <Link href="/" aria-label="LightEd home">
          <Logo />
        </Link>


        <div className="hidden items-center gap-3 md:flex">
          {!loading && user ? (
            <ButtonLink href={homeForRole(user.role)} size="sm">
              Go to dashboard
            </ButtonLink>
          ) : (
            <>
              <Link href="/login" className="px-3 text-sm font-semibold text-ink hover:text-brand-600">
                Log in
              </Link>
              <ButtonLink href="/register" size="sm">
                Get started free
              </ButtonLink>
            </>
          )}
        </div>

        <button
          className="rounded-xl p-2 text-ink md:hidden"
          onClick={() => setOpen((v) => !v)}
          aria-label="Toggle menu"
        >
          {open ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
        </button>
      </div>

      {open && (
        <div className="border-t border-line bg-white px-4 py-4 md:hidden">
          <div className="flex flex-col gap-3">
            <div className="mt-2 flex gap-3">
              <ButtonLink href="/login" variant="secondary" size="sm" className="flex-1">
                Log in
              </ButtonLink>
              <ButtonLink href="/register" size="sm" className="flex-1">
                Get started
              </ButtonLink>
            </div>
          </div>
        </div>
      )}
    </header>
  );
}
