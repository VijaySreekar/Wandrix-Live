import type { Metadata } from "next";
import {
  Cormorant_Garamond,
  Geist_Mono,
  Sora, Geist } from "next/font/google";
import Script from "next/script";

import { AppTopNav } from "@/components/app/app-top-nav";
import "./globals.css";
import { cn } from "@/lib/utils";

const geist = Geist({subsets:['latin'],variable:'--font-sans'});

const cormorant = Cormorant_Garamond({
  variable: "--font-display",
  subsets: ["latin"],
  weight: ["500", "600", "700"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

const sora = Sora({
  variable: "--font-brand",
  subsets: ["latin"],
  weight: ["600", "700"],
});

export const metadata: Metadata = {
  title: "Wandrix",
  description: "Next.js frontend paired with a FastAPI backend.",
};

export default async function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      suppressHydrationWarning
      className={cn("h-full", "antialiased", cormorant.variable, geistMono.variable, sora.variable, "font-sans", geist.variable)}
    >
      <head>
        <Script id="theme-init" strategy="beforeInteractive">{`
(() => {
  try {
    const storedTheme = localStorage.getItem("theme");
    const systemPrefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
    const theme = storedTheme === "dark" || storedTheme === "light"
      ? storedTheme
      : (systemPrefersDark ? "dark" : "light");

    const root = document.documentElement;
    root.classList.toggle("dark", theme === "dark");
    root.style.colorScheme = theme;

    const accentName = localStorage.getItem("accent");
    const accents = {
      wandr: { accent: "#1d4ed8", accent2: "#f4b400" },
      blue: { accent: "#2563eb", accent2: "#f4b400" },
      violet: { accent: "#7c3aed", accent2: "#ec4899" },
      emerald: { accent: "#059669", accent2: "#84cc16" },
      rose: { accent: "#e11d48", accent2: "#f59e0b" },
      amber: { accent: "#d97706", accent2: "#f43f5e" },
    };

    const palette = accents[accentName] ?? accents.wandr;
    root.style.setProperty("--accent", palette.accent);
    root.style.setProperty("--accent2", palette.accent2);

    const red = parseInt(palette.accent.slice(1, 3), 16);
    const green = parseInt(palette.accent.slice(3, 5), 16);
    const blue = parseInt(palette.accent.slice(5, 7), 16);
    const luminance = (0.2126 * red + 0.7152 * green + 0.0722 * blue) / 255;
    root.style.setProperty("--accent-foreground", luminance > 0.6 ? "#0a0a0a" : "#ffffff");
  } catch {}
})();
        `}</Script>
      </head>
      <body className="min-h-full bg-background text-foreground">
        <div className="flex min-h-screen flex-col">
          <AppTopNav />
          <div className="flex-1">{children}</div>
        </div>
      </body>
    </html>
  );
}
