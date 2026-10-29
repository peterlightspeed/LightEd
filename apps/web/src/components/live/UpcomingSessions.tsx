"use client";

import { useEffect, useState } from "react";
import { CalendarClock } from "lucide-react";

import { SessionRow } from "@/components/live/SessionsPanel";
import { Card } from "@/components/ui";
import { api } from "@/lib/api";
import type { LiveSessionItem } from "@/types";

/** Dashboard card: the next live classes across the user's courses. Renders nothing when there are none. */
export default function UpcomingSessions() {
  const [items, setItems] = useState<LiveSessionItem[]>([]);
  useEffect(() => {
    api.get<LiveSessionItem[]>("/sessions/upcoming").then(setItems).catch(() => undefined);
  }, []);
  if (items.length === 0) return null;
  return (
    <Card className="p-5 sm:p-6">
      <p className="flex items-center gap-2 font-display text-lg font-bold text-ink"><CalendarClock className="h-5 w-5 text-brand-600" /> Upcoming live classes</p>
      <div className="mt-2 divide-y divide-line/70">
        {items.map((s) => <SessionRow key={s.id} s={s} />)}
      </div>
    </Card>
  );
}
