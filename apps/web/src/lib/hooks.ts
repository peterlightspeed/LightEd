import { useEffect, useState } from "react";

/**
 * True once `active` has been true for `ms` milliseconds.
 * Used to tell people "the server is waking up" when free hosting cold-starts.
 */
export function useSlowHint(active: boolean, ms = 6000): boolean {
  const [slow, setSlow] = useState(false);
  useEffect(() => {
    if (!active) {
      setSlow(false);
      return;
    }
    const t = setTimeout(() => setSlow(true), ms);
    return () => clearTimeout(t);
  }, [active, ms]);
  return slow;
}
