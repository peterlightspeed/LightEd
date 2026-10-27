import { Badge } from "@/components/ui";
import type { Risk } from "@/types";

/** Low / medium / high risk pill (rule-based score, see backend services/analytics.py). */
export default function RiskBadge({ risk }: { risk: Risk }) {
  const tone = risk.band === "high" ? "rose" : risk.band === "medium" ? "amber" : "green";
  const label = risk.band === "high" ? "High risk" : risk.band === "medium" ? "Watch" : "On track";
  return <Badge tone={tone}>{label}</Badge>;
}
