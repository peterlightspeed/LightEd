"use client";

import { useRouter } from "next/navigation";
import { useEffect } from "react";

import { homeForRole } from "@/lib/auth";
import { useAuth } from "@/lib/auth-context";
import type { Role } from "@/types";

/** Page-level role guard: redirects other roles to their own home. Returns true when allowed. */
export function useRequireRole(roles: Role[]): boolean {
  const { user, loading } = useAuth();
  const router = useRouter();
  const allowed = !!user && roles.includes(user.role);
  useEffect(() => {
    if (!loading && user && !roles.includes(user.role)) router.replace(homeForRole(user.role));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [loading, user]);
  return allowed;
}
