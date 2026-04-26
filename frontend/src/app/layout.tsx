import type { Metadata } from "next";
import {
  Cormorant_Garamond,
  Geist_Mono,
  Sora, Geist } from "next/font/google";

import { AppearanceInitializer } from "@/components/app/appearance-initializer";
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
      <body className="min-h-full bg-background text-foreground">
        <AppearanceInitializer />
        <div className="flex min-h-screen flex-col">
          <AppTopNav />
          <div className="flex-1">{children}</div>
        </div>
      </body>
    </html>
  );
}
