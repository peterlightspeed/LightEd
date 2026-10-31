/**
 * Recognise what a teacher pasted as a "resource link" so students get the right experience:
 * YouTube / Vimeo / Instagram play inline, meeting recordings and Drive files get a labelled card.
 * Pure string parsing: no network calls, and embeds only ever point at the providers' own embed URLs.
 */
export type LinkKind = "youtube" | "vimeo" | "instagram" | "meeting" | "drive" | "link";
export interface LinkInfo {
  kind: LinkKind;
  label: string;
  embed?: string;
  portrait?: boolean;
}

const YT_ID = /^[\w-]{11}$/;

export function classifyLink(raw: string): LinkInfo {
  let u: URL;
  try {
    u = new URL(raw);
  } catch {
    return { kind: "link", label: "Link" };
  }
  const host = u.hostname.replace(/^(www\.|m\.)/, "").toLowerCase();
  const parts = u.pathname.split("/").filter(Boolean);

  if (host === "youtu.be" || host === "youtube.com" || host === "music.youtube.com") {
    const id = host === "youtu.be" ? parts[0] : u.searchParams.get("v") ?? (["shorts", "embed", "live"].includes(parts[0]) ? parts[1] : "");
    if (id && YT_ID.test(id)) return { kind: "youtube", label: "YouTube video", embed: `https://www.youtube-nocookie.com/embed/${id}` };
    return { kind: "link", label: "YouTube" };
  }
  if (host === "vimeo.com") {
    const id = parts.find((p) => /^\d+$/.test(p));
    if (id) return { kind: "vimeo", label: "Vimeo video", embed: `https://player.vimeo.com/video/${id}` };
  }
  if (host === "instagram.com") {
    const [type, code] = parts;
    if (["p", "reel", "reels", "tv"].includes(type) && code && /^[\w-]+$/.test(code)) {
      return { kind: "instagram", label: "Instagram video", embed: `https://www.instagram.com/${type === "reels" ? "reel" : type}/${code}/embed`, portrait: true };
    }
    return { kind: "link", label: "Instagram" };
  }
  if (/(^|\.)(zoom\.us|zoomgov\.com|webex\.com)$/.test(host) || host === "meet.google.com" || host === "teams.microsoft.com" || host === "teams.live.com") {
    return { kind: "meeting", label: "Recorded class / meeting" };
  }
  if (host === "drive.google.com" || host === "docs.google.com") return { kind: "drive", label: "Google Drive file" };
  return { kind: "link", label: host };
}
