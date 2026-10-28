"use client";

import { Moon, Sun } from "lucide-react";
import { useEffect, useState } from "react";

/** Light/dark switch. Saved in localStorage; the initial class is set by a script in layout.tsx. */
export default function ThemeToggle({ className = "" }: { className?: string }) {
  const [dark, setDark] = useState(false);
  useEffect(() => setDark(document.documentElement.classList.contains("dark")), []);

  function toggle() {
    const next = !dark;
    setDark(next);
    document.documentElement.classList.toggle("dark", next);
    try {
      localStorage.setItem("lighted_theme", next ? "dark" : "light");
    } catch {
      /* storage blocked: theme still applies for this visit */
    }
  }

  return (
    <button
      onClick={toggle}
      aria-label={dark ? "Switch to light mode" : "Switch to dark mode"}
      title={dark ? "Light mode" : "Dark mode"}
      className={`flex h-11 w-11 items-center justify-center rounded-xl text-muted hover:bg-mist hover:text-ink ${className}`}
    >
      {dark ? <Sun className="h-[18px] w-[18px]" /> : <Moon className="h-[18px] w-[18px]" />}
    </button>
  );
}
