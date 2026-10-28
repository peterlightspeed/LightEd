"use client";

import { useEffect, useState } from "react";
import { ExternalLink } from "lucide-react";

import { Card } from "@/components/ui";
import { api } from "@/lib/api";

/** "Go deeper" links a teacher attached to this lesson. Renders nothing if there are none. */
export default function Resources({ lessonId }: { lessonId: number }) {
  const [items, setItems] = useState<{ id: number; title: string; url: string }[]>([]);
  useEffect(() => {
    api.get<typeof items>(`/lessons/${lessonId}/resources`).then(setItems).catch(() => undefined);
  }, [lessonId]);
  if (items.length === 0) return null;
  return (
    <Card className="p-5 sm:p-6">
      <p className="font-display font-bold text-ink">Go deeper</p>
      <ul className="mt-2 divide-y divide-line/70">
        {items.map((r) => (
          <li key={r.id}>
            <a href={r.url} target="_blank" rel="noopener noreferrer" className="flex min-h-[48px] items-center justify-between gap-3 text-sm font-medium text-brand-600">
              <span className="min-w-0 truncate">{r.title}</span>
              <ExternalLink className="h-4 w-4 shrink-0" />
            </a>
          </li>
        ))}
      </ul>
    </Card>
  );
}
