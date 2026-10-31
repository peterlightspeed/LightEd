import type { ReactNode } from "react";

/**
 * Tiny, dependency-free renderer for the markdown subset LLMs actually produce:
 * paragraphs, "-"/"*" bullets, "1." lists, **bold**, *italic*, `code`.
 * It builds React nodes (never innerHTML), so model output can't inject markup.
 */
// NOTE: no lookbehind (`(?<!...)`): it is a parse-time SyntaxError on iOS < 16.4 and would break the whole bundle.
const INLINE = /(\*\*[^*\n]+\*\*|`[^`\n]+`|\*[^*\s][^*\n]*\*)/g;

function inline(text: string): ReactNode[] {
  const out: ReactNode[] = [];
  let last = 0;
  let i = 0;
  for (const m of text.matchAll(INLINE)) {
    const start = m.index ?? 0;
    if (start > last) out.push(text.slice(last, start));
    const tok = m[0];
    if (tok.startsWith("**")) out.push(<strong key={i++} className="font-semibold">{tok.slice(2, -2)}</strong>);
    else if (tok.startsWith("`")) out.push(<code key={i++} className="rounded bg-black/5 px-1 py-0.5 font-mono text-[0.85em] dark:bg-white/10">{tok.slice(1, -1)}</code>);
    else out.push(<em key={i++}>{tok.slice(1, -1)}</em>);
    last = start + tok.length;
  }
  if (last < text.length) out.push(text.slice(last));
  return out;
}

type Block = { kind: "p" | "ul" | "ol"; lines: string[] };

function toBlocks(text: string): Block[] {
  const blocks: Block[] = [];
  for (const raw of text.replace(/\r\n/g, "\n").split("\n")) {
    const line = raw.trimEnd();
    if (!line.trim()) {
      blocks.push({ kind: "p", lines: [] }); // blank line = paragraph break
      continue;
    }
    const ul = line.match(/^\s*[-*•]\s+(.*)$/);
    const ol = line.match(/^\s*\d+[.)]\s+(.*)$/);
    const kind = ul ? "ul" : ol ? "ol" : "p";
    const body = ul ? ul[1] : ol ? ol[1] : line.trim();
    const prev = blocks[blocks.length - 1];
    if (prev && prev.kind === kind && prev.lines.length > 0) prev.lines.push(body);
    else blocks.push({ kind, lines: [body] });
  }
  return blocks.filter((b) => b.lines.length > 0);
}

export function RichText({ text, className }: { text: string; className?: string }) {
  return (
    <div className={className}>
      {toBlocks(text).map((b, i) =>
        b.kind === "p" ? (
          <p key={i} className="[&:not(:first-child)]:mt-2">
            {b.lines.map((l, j) => (
              <span key={j}>
                {j > 0 && <br />}
                {inline(l)}
              </span>
            ))}
          </p>
        ) : b.kind === "ul" ? (
          <ul key={i} className="my-2 list-disc space-y-1 pl-5 first:mt-0 last:mb-0">
            {b.lines.map((l, j) => <li key={j}>{inline(l)}</li>)}
          </ul>
        ) : (
          <ol key={i} className="my-2 list-decimal space-y-1 pl-5 first:mt-0 last:mb-0">
            {b.lines.map((l, j) => <li key={j}>{inline(l)}</li>)}
          </ol>
        )
      )}
    </div>
  );
}
