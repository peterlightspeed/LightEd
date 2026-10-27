"use client";

/**
 * PWA glue:
 *  1) registers the service worker (production only),
 *  2) shows an "Install LightEd" alert:
 *       - Android/desktop Chrome: real install button (beforeinstallprompt),
 *       - iPhone/iPad Safari: step-by-step "Share → Add to Home Screen" (iOS has no install API),
 *  3) never nags: hidden when already installed, and dismissal is remembered for 7 days.
 */
import { useEffect, useState } from "react";
import Image from "next/image";
import { Download, Share, X } from "lucide-react";

interface InstallEvent extends Event {
  prompt: () => Promise<void>;
  userChoice: Promise<{ outcome: "accepted" | "dismissed" }>;
}

const KEY = "lighted_pwa_dismissed_at";
const WEEK = 7 * 24 * 3600 * 1000;

export default function PwaProvider() {
  const [deferred, setDeferred] = useState<InstallEvent | null>(null);
  const [ios, setIos] = useState(false);
  const [show, setShow] = useState(false);

  useEffect(() => {
    if ("serviceWorker" in navigator && process.env.NODE_ENV === "production") {
      navigator.serviceWorker.register("/sw.js").catch(() => undefined);
    }

    const standalone =
      window.matchMedia("(display-mode: standalone)").matches || (navigator as Navigator & { standalone?: boolean }).standalone;
    if (standalone) return; // already installed

    try {
      const t = Number(localStorage.getItem(KEY) || 0);
      if (t && Date.now() - t < WEEK) return;
    } catch {
      /* storage blocked — still allow the prompt */
    }

    const isIos = /iphone|ipad|ipod/i.test(navigator.userAgent) && !/crios|fxios/i.test(navigator.userAgent);
    const isMobile = /android|iphone|ipad|ipod/i.test(navigator.userAgent);
    let timer: ReturnType<typeof setTimeout>;

    const onPrompt = (e: Event) => {
      e.preventDefault(); // keep the event so OUR button can trigger the native dialog
      setDeferred(e as InstallEvent);
      timer = setTimeout(() => setShow(true), 6000);
    };
    window.addEventListener("beforeinstallprompt", onPrompt);

    if (isIos && isMobile) {
      setIos(true);
      timer = setTimeout(() => setShow(true), 8000);
    }
    window.addEventListener("appinstalled", () => setShow(false));
    return () => {
      window.removeEventListener("beforeinstallprompt", onPrompt);
      clearTimeout(timer);
    };
  }, []);

  function dismiss() {
    setShow(false);
    try {
      localStorage.setItem(KEY, String(Date.now()));
    } catch {
      /* ignore */
    }
  }

  async function install() {
    if (!deferred) return;
    await deferred.prompt();
    const choice = await deferred.userChoice;
    setDeferred(null);
    if (choice.outcome === "accepted") setShow(false);
    else dismiss();
  }

  if (!show || (!deferred && !ios)) return null;

  return (
    <div
      role="dialog"
      aria-label="Install LightEd"
      className="fixed inset-x-3 z-[90] mx-auto max-w-md rounded-3xl border border-line bg-white p-4 shadow-float"
      style={{ bottom: "calc(env(safe-area-inset-bottom) + 76px)" }} // sits above the mobile tab bar
    >
      <button onClick={dismiss} aria-label="Dismiss" className="absolute right-2 top-2 flex h-10 w-10 items-center justify-center rounded-xl text-muted hover:bg-mist">
        <X className="h-4 w-4" />
      </button>
      <div className="flex items-start gap-3 pr-8">
        <Image src="/icon-192.png" alt="" width={48} height={48} unoptimized className="rounded-2xl" />
        <div className="min-w-0">
          <p className="font-display text-base font-extrabold text-ink">Install LightEd</p>
          {ios ? (
            <p className="mt-0.5 text-sm text-muted">
              Add it to your home screen for faster access: tap <Share className="inline h-4 w-4 -translate-y-px text-brand-600" /> <b>Share</b>, then <b>Add to Home Screen</b>.
            </p>
          ) : (
            <p className="mt-0.5 text-sm text-muted">Get the app: opens instantly, works full-screen and feels like a native app.</p>
          )}
        </div>
      </div>
      <div className="mt-3 flex gap-2">
        {!ios && (
          <button onClick={install} className="inline-flex min-h-[44px] flex-1 items-center justify-center gap-2 rounded-xl bg-brand-600 px-4 text-sm font-semibold text-white hover:bg-brand-700">
            <Download className="h-4 w-4" /> Install app
          </button>
        )}
        <button onClick={dismiss} className="min-h-[44px] flex-1 rounded-xl border border-line px-4 text-sm font-semibold text-muted hover:bg-mist">
          Not now
        </button>
      </div>
    </div>
  );
}
