"use client";

/** Route-level error boundary for the signed-in app: the sidebar/top bar stay, only the page is replaced. */
import { useEffect } from "react";
import { RotateCcw } from "lucide-react";

import { Button, EmptyState } from "@/components/ui";

export default function AppError({ error, reset }: { error: Error & { digest?: string }; reset: () => void }) {
  useEffect(() => {
    console.error("Page crashed:", error);
  }, [error]);

  return (
    <div className="mx-auto max-w-lg py-10">
      <EmptyState
        title="This page hit a problem"
        description="Your data is safe. Try again, or reload the page. If it keeps happening, tell your teacher or LightEd support."
        action={
          <div className="flex flex-wrap justify-center gap-3">
            <Button onClick={reset}>
              <RotateCcw className="h-4 w-4" /> Try again
            </Button>
            <Button variant="secondary" onClick={() => window.location.reload()}>
              Reload page
            </Button>
          </div>
        }
      />
    </div>
  );
}
