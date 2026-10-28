"use client";

/** Header bell: unread badge + dropdown list (PDF FR-22). Polls every 60s; opening marks all read. */
import Link from "next/link";
import { useCallback, useEffect, useRef, useState } from "react";
import { Bell } from "lucide-react";

import { api } from "@/lib/api";
import { formatDate } from "@/lib/utils";

interface Item { id: number; kind: string; title: string; body: string; link: string; read: boolean; created_at: string | null }

export default function NotificationBell() {
  const [data, setData] = useState<{ unread: number; items: Item[] }>({ unread: 0, items: [] });
  const [open, setOpen] = useState(false);
  const box = useRef<HTMLDivElement>(null);

  const load = useCallback(() => {
    api.get<{ unread: number; items: Item[] }>("/notifications").then(setData).catch(() => undefined);
  }, []);

  useEffect(() => {
    load();
    const t = setInterval(load, 60000);
    return () => clearInterval(t);
  }, [load]);

  // Close when tapping outside.
  useEffect(() => {
    if (!open) return;
    const onDown = (e: MouseEvent | TouchEvent) => {
      if (box.current && !box.current.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener("mousedown", onDown);
    document.addEventListener("touchstart", onDown);
    return () => {
      document.removeEventListener("mousedown", onDown);
      document.removeEventListener("touchstart", onDown);
    };
  }, [open]);

  function toggle() {
    const next = !open;
    setOpen(next);
    if (next && data.unread > 0) {
      api.post("/notifications/read-all").then(() => setTimeout(load, 1500)).catch(() => undefined);
    }
  }

  return (
    <div className="relative" ref={box}>
      <button
        onClick={toggle}
        aria-label={`Notifications${data.unread ? `, ${data.unread} unread` : ""}`}
        className="relative flex h-11 w-11 items-center justify-center rounded-xl text-muted hover:bg-mist hover:text-ink"
      >
        <Bell className="h-[18px] w-[18px]" />
        {data.unread > 0 && (
          <span className="absolute right-1.5 top-1.5 flex h-4 min-w-[16px] items-center justify-center rounded-full bg-rose-500 px-1 text-[10px] font-bold text-white">
            {data.unread > 9 ? "9+" : data.unread}
          </span>
        )}
      </button>
      {open && (
        // Fixed + inset on phones so the panel never runs off-screen; anchored dropdown on desktop.
        <div className="fixed inset-x-3 top-[4.25rem] z-50 max-h-[70vh] overflow-y-auto rounded-2xl border border-line bg-white p-2 shadow-float sm:absolute sm:inset-x-auto sm:right-0 sm:top-12 sm:w-96">
          <p className="px-3 py-2 text-xs font-bold uppercase tracking-wider text-muted">Notifications</p>
          {data.items.length === 0 && <p className="px-3 py-6 text-center text-sm text-muted">You&apos;re all caught up 🎉</p>}
          {data.items.map((n) => {
            const inner = (
              <div className={`rounded-xl px-3 py-2.5 hover:bg-mist ${n.read ? "" : "bg-brand-50"}`}>
                <p className="text-sm font-semibold text-ink">{n.title}</p>
                {n.body && <p className="text-xs text-muted">{n.body}</p>}
                <p className="mt-0.5 text-[11px] text-muted">{formatDate(n.created_at)}</p>
              </div>
            );
            return n.link ? (
              <Link key={n.id} href={n.link} onClick={() => setOpen(false)}>{inner}</Link>
            ) : (
              <div key={n.id}>{inner}</div>
            );
          })}
        </div>
      )}
    </div>
  );
}
