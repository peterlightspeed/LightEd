/**
 * Session persistence helpers.
 *
 * The MVP stores the JWT in localStorage for speed. For a hardened production
 * build, move the refresh token to an httpOnly cookie (see GUIDE.md).
 */
import type { AuthResponse, User } from "@/types";

const TOKEN_KEY = "lighted_token";
const REFRESH_KEY = "lighted_refresh";
const USER_KEY = "lighted_user";

export function saveSession(data: AuthResponse) {
  if (typeof window === "undefined") return;
  localStorage.setItem(TOKEN_KEY, data.access_token);
  if (data.refresh_token) localStorage.setItem(REFRESH_KEY, data.refresh_token);
  localStorage.setItem(USER_KEY, JSON.stringify(data.user));
}

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(TOKEN_KEY);
}

export function getStoredUser(): User | null {
  if (typeof window === "undefined") return null;
  try {
    const raw = localStorage.getItem(USER_KEY);
    return raw ? (JSON.parse(raw) as User) : null;
  } catch {
    return null;
  }
}

export function clearSession() {
  if (typeof window === "undefined") return;
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(REFRESH_KEY);
  localStorage.removeItem(USER_KEY);
}

export function isAuthenticated(): boolean {
  return Boolean(getToken());
}

/** Where each role lands after login. */
export function homeForRole(role?: string | null): string {
  if (role === "teacher") return "/dashboard/teacher";
  if (role === "admin") return "/dashboard/admin";
  return "/dashboard";
}
