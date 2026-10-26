"use client";

/**
 * AuthProvider keeps the current user in React state and mirrors it to
 * localStorage so a refresh does not log the user out.
 *
 * This is intentionally small: JWT only, no refresh-token rotation loop yet.
 */
import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";

import { api } from "@/lib/api";
import {
  clearSession,
  getStoredUser,
  getToken,
  homeForRole,
  saveSession,
} from "@/lib/auth";
import type { AuthResponse, User } from "@/types";

interface AuthContextValue {
  user: User | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<User>;
  register: (payload: {
    full_name: string;
    email: string;
    password: string;
    role: string;
  }) => Promise<User>;
  logout: () => void;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const router = useRouter();

  // Hydrate from localStorage, then verify the token with /auth/me.
  useEffect(() => {
    const cached = getStoredUser();
    if (cached) setUser(cached);

    if (!getToken()) {
      setLoading(false);
      return;
    }
    api
      .get<User>("/auth/me")
      .then((fresh) => {
        setUser(fresh);
        localStorage.setItem("lighted_user", JSON.stringify(fresh));
      })
      .catch(() => {
        clearSession();
        setUser(null);
      })
      .finally(() => setLoading(false));
  }, []);

  const login = useCallback(async (email: string, password: string) => {
    const data = await api.post<AuthResponse>("/auth/login", { email, password }, false);
    saveSession(data);
    setUser(data.user);
    return data.user;
  }, []);

  const register = useCallback(
    async (payload: { full_name: string; email: string; password: string; role: string }) => {
      const data = await api.post<AuthResponse>("/auth/register", payload, false);
      saveSession(data);
      setUser(data.user);
      return data.user;
    },
    []
  );

  const logout = useCallback(() => {
    clearSession();
    setUser(null);
    router.push("/login");
  }, [router]);

  const refreshUser = useCallback(async () => {
    const fresh = await api.get<User>("/auth/me");
    setUser(fresh);
  }, []);

  const value = useMemo(
    () => ({ user, loading, login, register, logout, refreshUser }),
    [user, loading, login, register, logout, refreshUser]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used inside <AuthProvider>");
  return ctx;
}

export { homeForRole };
