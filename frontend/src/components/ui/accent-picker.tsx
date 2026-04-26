"use client";

import { Check, Palette } from "lucide-react";
import { useEffect, useRef, useState, useSyncExternalStore } from "react";

type AccentName = "emerald" | "violet" | "rose" | "amber";

const ACCENTS: Record<
  AccentName,
  { label: string; accent: string; accent2: string }
> = {
  emerald: { label: "Wandrix", accent: "#059669", accent2: "#84cc16" },
  violet: { label: "Violet + Pink", accent: "#7c3aed", accent2: "#ec4899" },
  rose: { label: "Rose + Amber", accent: "#e11d48", accent2: "#f59e0b" },
  amber: { label: "Amber + Rose", accent: "#d97706", accent2: "#f43f5e" },
};

function getCurrentAccent(): AccentName {
  if (typeof window === "undefined") {
    return "emerald";
  }

  try {
    const stored = localStorage.getItem("accent");
    if (
      stored === "emerald" ||
      stored === "violet" ||
      stored === "rose" ||
      stored === "amber"
    ) {
      return stored;
    }
  } catch {}

  return "emerald";
}

function subscribe(onStoreChange: () => void) {
  if (typeof window === "undefined") {
    return () => {};
  }

  const onStorage = (event: StorageEvent) => {
    if (event.key === "accent") {
      onStoreChange();
    }
  };

  window.addEventListener("storage", onStorage);
  window.addEventListener("accentchange", onStoreChange);

  return () => {
    window.removeEventListener("storage", onStorage);
    window.removeEventListener("accentchange", onStoreChange);
  };
}

function applyAccent(accent: AccentName) {
  const root = document.documentElement;
  const palette = ACCENTS[accent];
  root.style.setProperty("--accent", palette.accent);
  root.style.setProperty("--accent2", palette.accent2);

  const red = parseInt(palette.accent.slice(1, 3), 16);
  const green = parseInt(palette.accent.slice(3, 5), 16);
  const blue = parseInt(palette.accent.slice(5, 7), 16);
  const luminance = (0.2126 * red + 0.7152 * green + 0.0722 * blue) / 255;
  root.style.setProperty(
    "--accent-foreground",
    luminance > 0.6 ? "#0a0a0a" : "#ffffff",
  );

  try {
    localStorage.setItem("accent", accent);
  } catch {}

  window.dispatchEvent(new Event("accentchange"));
}

export function AccentPicker() {
  const accent = useSyncExternalStore(subscribe, getCurrentAccent, () => "emerald");
  const [isOpen, setIsOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!isOpen) {
      return;
    }

    const handlePointerDown = (event: MouseEvent) => {
      if (!containerRef.current?.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        setIsOpen(false);
      }
    };

    window.addEventListener("mousedown", handlePointerDown);
    window.addEventListener("keydown", handleKeyDown);

    return () => {
      window.removeEventListener("mousedown", handlePointerDown);
      window.removeEventListener("keydown", handleKeyDown);
    };
  }, [isOpen]);

  return (
    <div className="relative" ref={containerRef}>
      <button
        type="button"
        onClick={() => setIsOpen((current) => !current)}
        aria-label="Accent color"
        aria-expanded={isOpen}
        className="relative inline-grid h-10 w-10 place-items-center rounded-full border border-transparent bg-transparent text-[color:var(--nav-utility-icon)] transition-colors hover:bg-[color:var(--nav-hover)] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[color:var(--nav-utility-border)]"
      >
        <Palette className="h-4 w-4" />
      </button>

      {isOpen ? (
        <div className="absolute right-0 top-12 z-50 min-w-56 rounded-[1.35rem] border border-[color:var(--nav-border)] bg-[color:var(--nav-shell)] p-2 shadow-[var(--nav-shadow)]">
          {(Object.keys(ACCENTS) as AccentName[]).map((key) => {
            const isActive = accent === key;
            const palette = ACCENTS[key];

            return (
              <button
                key={key}
                type="button"
                onClick={() => {
                  applyAccent(key);
                  setIsOpen(false);
                }}
                className="flex w-full items-center gap-3 rounded-2xl px-3 py-2 text-left text-sm transition-colors hover:bg-[color:var(--nav-hover)]"
              >
                <span
                  className="h-3.5 w-3.5 rounded-full ring-1 ring-border"
                  style={{
                    backgroundImage: `linear-gradient(135deg, ${palette.accent}, ${palette.accent2})`,
                  }}
                  aria-hidden="true"
                />
                <span className="flex-1">{palette.label}</span>
                {isActive ? (
                  <Check className="h-4 w-4 text-[color:var(--nav-brand-mark)]" />
                ) : null}
              </button>
            );
          })}
        </div>
      ) : null}
    </div>
  );
}
