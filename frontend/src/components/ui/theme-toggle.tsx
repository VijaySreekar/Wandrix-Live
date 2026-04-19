"use client";

import { Moon, Sun } from "lucide-react";
import { useSyncExternalStore } from "react";

type Theme = "light" | "dark";

function getCurrentTheme(): Theme {
  if (typeof document === "undefined") {
    return "light";
  }

  return document.documentElement.classList.contains("dark") ? "dark" : "light";
}

function subscribe(onStoreChange: () => void) {
  if (typeof window === "undefined" || typeof document === "undefined") {
    return () => {};
  }

  const root = document.documentElement;
  const observer = new MutationObserver(() => onStoreChange());
  observer.observe(root, { attributes: true, attributeFilter: ["class"] });

  const onStorage = (event: StorageEvent) => {
    if (event.key === "theme") {
      onStoreChange();
    }
  };

  window.addEventListener("storage", onStorage);
  window.addEventListener("themechange", onStoreChange);

  return () => {
    observer.disconnect();
    window.removeEventListener("storage", onStorage);
    window.removeEventListener("themechange", onStoreChange);
  };
}

function applyTheme(theme: Theme) {
  const root = document.documentElement;
  root.classList.toggle("dark", theme === "dark");
  root.style.colorScheme = theme;

  try {
    localStorage.setItem("theme", theme);
  } catch {}

  window.dispatchEvent(new Event("themechange"));
}

export function ThemeToggle() {
  const theme = useSyncExternalStore(subscribe, getCurrentTheme, () => "light");
  const isDark = theme === "dark";

  return (
    <button
      type="button"
      onClick={() => applyTheme(isDark ? "light" : "dark")}
      aria-label="Toggle theme"
      aria-pressed={isDark}
      className="relative inline-grid h-10 w-10 place-items-center rounded-xl bg-transparent text-foreground transition-colors hover:bg-muted focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent/40"
    >
      <Sun
        className={[
          "absolute h-4 w-4 transition-all duration-300",
          isDark ? "scale-0 rotate-90 opacity-0" : "scale-100 rotate-0 opacity-100",
        ].join(" ")}
      />
      <Moon
        className={[
          "absolute h-4 w-4 transition-all duration-300",
          isDark ? "scale-100 rotate-0 opacity-100" : "scale-0 -rotate-90 opacity-0",
        ].join(" ")}
      />
    </button>
  );
}
