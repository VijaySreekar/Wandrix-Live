"use client";

import { useLayoutEffect } from "react";

type AccentPalette = {
  accent: string;
  accent2: string;
};

const ACCENTS: Record<string, AccentPalette> = {
  violet: { accent: "#7c3aed", accent2: "#ec4899" },
  emerald: { accent: "#059669", accent2: "#84cc16" },
  rose: { accent: "#e11d48", accent2: "#f59e0b" },
  amber: { accent: "#d97706", accent2: "#f43f5e" },
};

function applyAppearance() {
  const root = document.documentElement;

  const theme = localStorage.getItem("theme");
  const isDark = theme === "dark";
  root.classList.toggle("dark", isDark);
  root.style.colorScheme = isDark ? "dark" : "light";

  const accentName = localStorage.getItem("accent") ?? "emerald";
  const palette = ACCENTS[accentName] ?? ACCENTS.emerald;
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
}

export function AppearanceInitializer() {
  useLayoutEffect(() => {
    applyAppearance();

    const syncAppearance = () => applyAppearance();
    window.addEventListener("storage", syncAppearance);
    window.addEventListener("themechange", syncAppearance);
    window.addEventListener("accentchange", syncAppearance);

    return () => {
      window.removeEventListener("storage", syncAppearance);
      window.removeEventListener("themechange", syncAppearance);
      window.removeEventListener("accentchange", syncAppearance);
    };
  }, []);

  return null;
}
