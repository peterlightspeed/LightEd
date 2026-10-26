"use client";

/**
 * "Continue with Google" using Google Identity Services (GIS).
 *
 * How it works:
 *  1. We ask the API which Google client id is configured (GET /auth/providers),
 *     falling back to NEXT_PUBLIC_GOOGLE_CLIENT_ID.
 *  2. If none is configured the component renders NOTHING (email login still works).
 *  3. Otherwise we load Google's script, render their official button, and when the
 *     user picks an account we POST the returned ID token to /auth/google.
 */
import { useRouter } from "next/navigation";
import { useEffect, useRef, useState } from "react";

import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";
import { homeForRole } from "@/lib/auth";

/* Minimal typing for the bits of the GIS global we use. */
interface GoogleId {
  initialize: (cfg: { client_id: string; callback: (r: { credential: string }) => void; ux_mode?: string }) => void;
  renderButton: (el: HTMLElement, opts: Record<string, unknown>) => void;
}
declare global {
  interface Window {
    google?: { accounts: { id: GoogleId } };
  }
}

const GSI_SRC = "https://accounts.google.com/gsi/client";

function loadGsi(): Promise<void> {
  return new Promise((resolve, reject) => {
    if (window.google?.accounts?.id) return resolve();
    const existing = document.querySelector<HTMLScriptElement>(`script[src="${GSI_SRC}"]`);
    if (existing) {
      existing.addEventListener("load", () => resolve());
      existing.addEventListener("error", () => reject(new Error("gsi")));
      return;
    }
    const s = document.createElement("script");
    s.src = GSI_SRC;
    s.async = true;
    s.defer = true;
    s.onload = () => resolve();
    s.onerror = () => reject(new Error("gsi"));
    document.head.appendChild(s);
  });
}

export default function GoogleButton({ role, label = "or continue with" }: { role?: string; label?: string }) {
  const router = useRouter();
  const { googleLogin } = useAuth();
  const holder = useRef<HTMLDivElement>(null);
  const roleRef = useRef(role);
  roleRef.current = role; // always use the latest selected role inside the GIS callback

  const [clientId, setClientId] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // 1) Discover the client id.
  useEffect(() => {
    const fallback = process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID || null;
    api
      .get<{ google_client_id: string | null }>("/auth/providers", false)
      .then((d) => setClientId(d.google_client_id || fallback))
      .catch(() => setClientId(fallback));
  }, []);

  // 2) Load GIS and render Google's button.
  useEffect(() => {
    if (!clientId || !holder.current) return;
    let cancelled = false;
    loadGsi()
      .then(() => {
        if (cancelled || !window.google || !holder.current) return;
        window.google.accounts.id.initialize({
          client_id: clientId,
          callback: async ({ credential }) => {
            setError(null);
            setBusy(true);
            try {
              const user = await googleLogin(credential, roleRef.current);
              router.push(homeForRole(user.role));
            } catch (err) {
              setError(err instanceof Error ? err.message : "Google sign-in failed. Please try again.");
              setBusy(false);
            }
          },
        });
        window.google.accounts.id.renderButton(holder.current, {
          theme: "outline",
          size: "large",
          shape: "rectangular",
          text: "continue_with",
          logo_alignment: "left",
          width: Math.min(400, holder.current.offsetWidth || 360),
        });
      })
      .catch(() => setError("Couldn't load Google sign-in. Check your connection or use email."));
    return () => {
      cancelled = true;
    };
  }, [clientId, googleLogin, router]);

  if (!clientId) return null; // Google not configured -> hide gracefully

  return (
    <div className="mt-6">
      <div className="relative flex items-center">
        <span className="h-px flex-1 bg-line" />
        <span className="px-3 text-xs font-medium uppercase tracking-wider text-muted">{label}</span>
        <span className="h-px flex-1 bg-line" />
      </div>
      <div className="mt-4 flex min-h-[44px] justify-center" aria-busy={busy}>
        <div ref={holder} className={busy ? "pointer-events-none opacity-50" : ""} style={{ width: "100%", display: "flex", justifyContent: "center" }} />
      </div>
      {busy && <p className="mt-2 text-center text-xs text-muted">Signing you in…</p>}
      {error && (
        <p className="mt-3 rounded-xl border border-rose-200 bg-rose-50 px-4 py-2.5 text-sm font-medium text-rose-700">{error}</p>
      )}
    </div>
  );
}
