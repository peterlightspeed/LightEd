/**
 * Original flat illustrations of people (SVG, no licensing issues, no network requests).
 * They add the human feel the landing/auth pages were missing. Swap in real, consented photos of your
 * own students/teachers any time: see public/people/README.md.
 */

type Style = "short" | "long" | "afro" | "cap";
export interface PersonLook {
  skin: string;
  hair: string;
  shirt: string;
  style: Style;
}

export const LOOKS: PersonLook[] = [
  { skin: "#8d5524", hair: "#1f1a17", shirt: "#2f6bff", style: "short" },
  { skin: "#e0ac69", hair: "#3b2a20", shirt: "#f5b414", style: "long" },
  { skin: "#5c3a21", hair: "#15110f", shirt: "#10b981", style: "afro" },
  { skin: "#f1c9a5", hair: "#6b3f1d", shirt: "#7c3aed", style: "long" },
  { skin: "#c68642", hair: "#1f1a17", shirt: "#f43f5e", style: "short" },
  { skin: "#a8693a", hair: "#241b16", shirt: "#1a3572", style: "cap" },
];

/** A head-and-shoulders figure drawn in a 100x100 box. Used inside other <svg>s via transform. */
export function PersonGlyph({ skin, hair, shirt, style }: PersonLook) {
  return (
    <g>
      {/* hair behind the head */}
      {style === "long" && <path d="M26 44c0-20 10-30 24-30s24 10 24 30v26H26z" fill={hair} />}
      {style === "afro" && <circle cx="50" cy="38" r="27" fill={hair} />}
      {/* shoulders + neck */}
      <path d="M12 100c0-20 16-34 38-34s38 14 38 34z" fill={shirt} />
      <rect x="43" y="52" width="14" height="18" rx="6" fill={skin} />
      {/* head */}
      <circle cx="50" cy="40" r="19" fill={skin} />
      {/* hair on top */}
      {style === "short" && <path d="M31 38c0-14 8-20 19-20s19 6 19 20c-6-6-13-8-19-8s-13 2-19 8z" fill={hair} />}
      {style === "long" && <path d="M31 40c0-15 8-22 19-22s19 7 19 22c-4-9-10-13-19-13s-15 4-19 13z" fill={hair} />}
      {style === "afro" && <path d="M33 36c2-10 9-14 17-14s15 4 17 14c-5-4-11-6-17-6s-12 2-17 6z" fill={hair} />}
      {style === "cap" && (
        <>
          <path d="M30 36c0-13 8-19 20-19s20 6 20 19z" fill={hair} />
          <rect x="28" y="34" width="44" height="5" rx="2.5" fill={hair} />
        </>
      )}
      {/* face */}
      <circle cx="43" cy="42" r="1.8" fill="#1a1a1a" />
      <circle cx="57" cy="42" r="1.8" fill="#1a1a1a" />
      <path d="M44 49c3 3 9 3 12 0" stroke="#1a1a1a" strokeWidth="1.8" fill="none" strokeLinecap="round" />
    </g>
  );
}

/** Round avatar. */
export function Avatar({ look, size = 44, bg = "#dbe7ff" }: { look: PersonLook; size?: number; bg?: string }) {
  return (
    <svg width={size} height={size} viewBox="0 0 100 100" aria-hidden className="rounded-full">
      <rect width="100" height="100" fill={bg} />
      <g transform="translate(0 8)">
        <PersonGlyph {...look} />
      </g>
    </svg>
  );
}

/** Overlapping group of avatars: "learners and teachers like you". */
export function AvatarGroup({ size = 44 }: { size?: number }) {
  const bgs = ["#dbe7ff", "#fff1c9", "#d8f5ea", "#ece3ff", "#ffe0e6"];
  return (
    <div className="flex -space-x-3" aria-hidden>
      {LOOKS.slice(0, 5).map((l, i) => (
        <span key={i} className="inline-block overflow-hidden rounded-full ring-4 ring-white dark:ring-transparent">
          <Avatar look={l} size={size} bg={bgs[i]} />
        </span>
      ))}
    </div>
  );
}

/** Hero scene: a student studying with an AI tutor. Chips contain no personal data. */
export function StudentScene({ className = "" }: { className?: string }) {
  return (
    <svg viewBox="0 0 440 360" className={className} role="img" aria-label="A student learning on a laptop with an AI tutor helping">
      <ellipse cx="225" cy="200" rx="200" ry="150" fill="#dbe7ff" />
      <circle cx="372" cy="70" r="34" fill="#ffe7a3" />
      {/* student (back) */}
      <g transform="translate(120 70) scale(2.1)">
        <PersonGlyph {...LOOKS[2]} />
      </g>
      {/* desk */}
      <rect x="40" y="262" width="360" height="16" rx="8" fill="#1a3572" />
      <rect x="70" y="278" width="10" height="56" rx="4" fill="#142a5c" />
      <rect x="360" y="278" width="10" height="56" rx="4" fill="#142a5c" />
      {/* laptop */}
      <rect x="150" y="196" width="150" height="68" rx="8" fill="#0f1f46" />
      <rect x="158" y="203" width="134" height="54" rx="4" fill="#ffffff" />
      <rect x="166" y="213" width="64" height="7" rx="3.5" fill="#2f6bff" />
      <rect x="166" y="227" width="94" height="7" rx="3.5" fill="#dbe7ff" />
      <rect x="166" y="241" width="48" height="7" rx="3.5" fill="#10b981" />
      <circle cx="268" cy="222" r="14" fill="none" stroke="#dbe7ff" strokeWidth="6" />
      <path d="M268 208a14 14 0 1 1-13.3 9.7" fill="none" stroke="#f5b414" strokeWidth="6" strokeLinecap="round" />
      <path d="M130 264h190l-10 10H140z" fill="#142a5c" />
      {/* book + plant */}
      <rect x="62" y="248" width="52" height="14" rx="3" fill="#f5b414" />
      <rect x="66" y="236" width="44" height="12" rx="3" fill="#f43f5e" />
      <path d="M346 262c-4-22 2-36 12-44-2 14 4 26 14 44z" fill="#10b981" />
      {/* floating chips */}
      <g transform="translate(30 70)">
        <rect width="150" height="54" rx="16" fill="#fff" stroke="#e4e9f5" />
        <circle cx="26" cy="27" r="14" fill="#eef4ff" />
        <path d="M26 19l2.6 5.4 5.9.8-4.3 4.1 1 5.8-5.2-2.8-5.2 2.8 1-5.8-4.3-4.1 5.9-.8z" fill="#2f6bff" />
        <text x="50" y="24" fontSize="11" fontWeight="700" fill="#0f1b33">AI tutor</text>
        <text x="50" y="40" fontSize="10" fill="#6b7a99">Need a hint?</text>
      </g>
      <g transform="translate(292 118)">
        <rect width="124" height="50" rx="16" fill="#fff" stroke="#e4e9f5" />
        <circle cx="26" cy="25" r="13" fill="#d8f5ea" />
        <path d="M20 25l4 4 8-9" stroke="#10b981" strokeWidth="3" fill="none" strokeLinecap="round" strokeLinejoin="round" />
        <text x="46" y="22" fontSize="11" fontWeight="700" fill="#0f1b33">Quiz done</text>
        <text x="46" y="38" fontSize="10" fill="#6b7a99">Great work!</text>
      </g>
    </svg>
  );
}

/** Teacher at the board with a small class: used in the "for teachers" card. */
export function TeacherScene({ className = "" }: { className?: string }) {
  return (
    <svg viewBox="0 0 440 300" className={className} role="img" aria-label="A teacher presenting to a class">
      <ellipse cx="220" cy="170" rx="200" ry="120" fill="#fff1c9" />
      {/* board */}
      <rect x="40" y="26" width="260" height="140" rx="14" fill="#1a3572" />
      <rect x="52" y="38" width="236" height="116" rx="8" fill="#22448f" />
      <rect x="72" y="104" width="26" height="40" rx="4" fill="#f5b414" />
      <rect x="110" y="84" width="26" height="60" rx="4" fill="#ffffff" />
      <rect x="148" y="64" width="26" height="80" rx="4" fill="#2f6bff" />
      <rect x="186" y="94" width="26" height="50" rx="4" fill="#10b981" />
      <path d="M72 70l60-14 52 8 70-22" stroke="#ffe7a3" strokeWidth="3" fill="none" strokeLinecap="round" />
      <rect x="232" y="46" width="42" height="14" rx="7" fill="#ffffff" opacity=".25" />
      {/* teacher */}
      <g transform="translate(300 40) scale(1.7)">
        <PersonGlyph {...LOOKS[3]} />
      </g>
      {/* class */}
      <rect x="20" y="236" width="400" height="12" rx="6" fill="#142a5c" opacity=".12" />
      {[LOOKS[0], LOOKS[4], LOOKS[1], LOOKS[5]].map((l, i) => (
        <g key={i} transform={`translate(${52 + i * 88} 168) scale(0.85)`}>
          <PersonGlyph {...l} />
        </g>
      ))}
    </svg>
  );
}
