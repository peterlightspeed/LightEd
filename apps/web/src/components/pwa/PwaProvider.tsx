"use client";

/**
 * PWA glue — deliberately polite:
 *  - registers the service worker (production only);
 *  - shows ONE small "Install LightEd" card, only inside the signed-in app (never on landing/login),
 *    only after the user has spent ~25 s in the app;
 *  - the moment it is shown it is "used up": it will not come back for 14 days (even if ignored or
 *    the page is reloaded). "Install" or "Not now" lock it for 30 days. Already-installed = never.
 *  - Android/desktop Chrome get the real install button; iPhone Safari gets Share -> Add to Home Screen steps.
 */
import { useEffect, useRef, useState } from "react";
import { usePathname } from "next/navigation";
import Image from "next/image";
import { Download, Share, X } from "lucide-react";

interface InstallEvent extends Event {
  prompt: () => Promise<void>;
  userChoice: Promise<{ outcome: "accepted" | "dismissed" }>;
}

const KEY = "lighted_pwa_next_prompt"; // epoch ms before which we stay quiet
const DAY = 24 * 3600 * 1000;
const APP_PREFIXES = ["/dashboard", "/courses", "/lessons", "/quizzes", "/progress", "/students", "/planner", "/tutor"];

const quietUntil = () => {
  try { return Number(localStorage.getItem(KEY) || 0); } catch { return 0; }
};
const stayQuiet = (days: number) => {
  try { localStorage.setItem(KEY, String(Date.now() + days * DAY)); } catch { /* ignore */ }
};

export default function PwaProvider() {
  const pathname = usePathname();
  const inApp = APP_PREFIXES.some((p) => pathname.startsWith(p));
  const deferred = useRef<InstallEvent | null>(null);
  const timer = useRef<ReturnType<typeof setTimeout>>();
  const [ios, setIos] = useState(false);
  const [show, setShow] = useState(false);
  const [canPrompt, setCanPrompt] = useState(false);

  // 1) Service worker + capture the browser's install event (once, for the whole session).
  useEffect(() => {
    if ("serviceWorker" in navigator && process.env.NODE_ENV === "production") {
      navigator.serviceWorker.register("/sw.js").catch(() => undefined);
    }
    const onPrompt = (e: Event) => {
      e.preventDefault(); // we show our own UI instead of Chrome's mini-bar
      deferred.current = e as InstallEvent;
      setCanPrompt(true);
    };
    const onInstalled = () => { stayQuiet(3650); setShow(false); };
    window.addEventListener("beforeinstallprompt", onPrompt);
    window.addEventListener("appinstalled", onInstalled);
    const ua = navigator.userAgent;
    setIos(/iphone|ipad|ipod/i.test(ua) && !/crios|fxios/i.test(ua));
    return () => {
      window.removeEventListener("beforeinstallprompt", onPrompt);
      window.removeEventListener("appinstalled", onInstalled);
    };
  }, []);

  // 2) Decide WHEN to show: in-app only, not installed, not recently shown, after ~25 s.
  useEffect(() => {
    clearTimeout(timer.current);
    if (!inApp || show) return;
    const standalone =
      window.matchMedia("(display-mode: standalone)").matches ||
      (navigator as Navigator & { standalone?: boolean }).standalone;
    if (standalone || Date.now() < quietUntil()) return;
    if (!canPrompt && !ios) return; // nothing installable on this browser
    timer.current = setTimeout(() => {
      if (Date.now() < quietUntil()) return;
      stayQuiet(14); // "used up" immediately, so reloads/navigation can't re-trigger it
      setShow(true);
    }, 25000);
    return () => clearTimeout(timer.current);
  }, [inApp, canPrompt, ios, show]);

  function close() {
    stayQuiet(30);
    setShow(false);
  }

  async function install() {
    const ev = deferred.current;
    deferred.current = null;
    setCanPrompt(false);
    setShow(false);
    stayQuiet(30);
    if (ev) {
      try {
        await ev.prompt();
        await ev.userChoice;
      } catch {
        /* prompt() can only be used once; ignore */
      }
    }
  }

  if (!show || !inApp) return null;

  return (
    <div
      role="dialog"
      aria-label="Install LightEd"
      className="fixed inset-x-3 z-[60] mx-auto max-w-sm rounded-2xl border border-line bg-white p-3.5 shadow-float"
      style={{ bottom: "calc(env(safe-area-inset-bottom) + 76px)" }} // above the mobile tab bar
    >
      <button onClick={close} aria-label="Dismiss" className="absolute right-1 top-1 flex h-9 w-9 items-center justify-center rounded-xl text-muted hover:bg-mist">
        <X className="h-4 w-4" />
      </button>
      <div className="flex items-start gap-3 pr-7">
        <Image src="/icon-192.png" alt="" width={40} height={40} unoptimized className="h-10 w-10 shrink-0 rounded-xl" />
        <div className="min-w-0">
          <p className="font-display text-sm font-extrabold text-ink">Install LightEd</p>
          {ios ? (
            <p className="mt-0.5 text-xs leading-5 text-muted">
              Tap <Share className="inline h-3.5 w-3.5 -translate-y-px text-brand-600" /> <b>Share</b>, then <b>Add to Home Screen</b>.
            </p>
          ) : (
            <p className="mt-0.5 text-xs leading-5 text-muted">Open it like an app, full-screen and fast.</p>
          )}
        </div>
      </div>
      <div className="mt-3 flex gap-2">
        {!ios && (
          <button onClick={install} className="inline-flex min-h-[40px] flex-1 items-center justify-center gap-1.5 rounded-xl bg-brand-600 px-3 text-sm font-semibold text-white hover:bg-brand-700">
            <Download className="h-4 w-4" /> Install
          </button>
        )}
        <button onClick={close} className="min-h-[40px] flex-1 rounded-xl border border-line px-3 text-sm font-semibold text-muted hover:bg-mist">
          Not now
        </button>
      </div>
    </div>
  );
}
