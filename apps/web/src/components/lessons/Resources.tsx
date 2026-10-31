"use client";

import { useEffect, useState } from "react";
import { ExternalLink, FileText, Link2, PlayCircle, Video } from "lucide-react";

import { Card } from "@/components/ui";
import { api } from "@/lib/api";
import { classifyLink } from "@/lib/media";

interface Item {
  id: number;
  title: string;
  url: string;
}

/** Videos and extra material a teacher attached to this lesson. Renders nothing if there are none. */
export default function Resources({ lessonId }: { lessonId: number }) {
  const [items, setItems] = useState<Item[]>([]);
  useEffect(() => {
    api.get<Item[]>(`/lessons/${lessonId}/resources`).then(setItems).catch(() => undefined);
  }, [lessonId]);
  if (items.length === 0) return null;

  return (
    <Card className="p-5 sm:p-6">
      <p className="font-display font-bold text-ink">Videos &amp; materials</p>
      <ul className="mt-3 space-y-4">
        {items.map((r) => {
          const info = classifyLink(r.url);
          const Icon = info.kind === "meeting" ? Video : info.kind === "drive" ? FileText : info.kind === "link" ? Link2 : PlayCircle;
          return (
            <li key={r.id}>
              {info.embed ? (
                <div>
                  <div className={`overflow-hidden rounded-2xl bg-black ${info.portrait ? "mx-auto max-w-[360px]" : "aspect-video w-full"}`}>
                    <iframe
                      src={info.embed}
                      title={r.title}
                      loading="lazy"
                      allowFullScreen
                      referrerPolicy="strict-origin-when-cross-origin"
                      sandbox="allow-scripts allow-same-origin allow-presentation allow-popups allow-popups-to-escape-sandbox"
                      className={info.portrait ? "h-[520px] w-full" : "h-full w-full"}
                    />
                  </div>
                  <a href={r.url} target="_blank" rel="noopener noreferrer" className="mt-2 flex min-h-[44px] items-center justify-between gap-3 text-sm font-medium text-brand-600">
                    <span className="min-w-0 truncate">{r.title}</span>
                    <span className="flex shrink-0 items-center gap-1 text-xs text-muted">Open {info.label.split(" ")[0]} <ExternalLink className="h-3.5 w-3.5" /></span>
                  </a>
                </div>
              ) : (
                <a href={r.url} target="_blank" rel="noopener noreferrer" className="flex min-h-[56px] items-center gap-3 rounded-2xl border border-line px-4 py-2 hover:bg-mist">
                  <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-brand-50 text-brand-600"><Icon className="h-5 w-5" /></span>
                  <span className="min-w-0 flex-1">
                    <span className="block truncate text-sm font-semibold text-ink">{r.title}</span>
                    <span className="block truncate text-xs text-muted">{info.label}</span>
                  </span>
                  <ExternalLink className="h-4 w-4 shrink-0 text-muted" />
                </a>
              )}
            </li>
          );
        })}
      </ul>
    </Card>
  );
}
