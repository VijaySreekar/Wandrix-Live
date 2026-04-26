import type { Metadata } from "next";
import {
  Cormorant_Garamond,
  Geist,
  Geist_Mono,
  Sora,
} from "next/font/google";

import { AppearanceInitializer } from "@/components/app/appearance-initializer";
import { AppTopNav } from "@/components/app/app-top-nav";
import "./globals.css";
import { cn } from "@/lib/utils";

const geist = Geist({
  subsets: ["latin"],
  variable: "--font-sans",
});

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

const siteUrl = process.env.NEXT_PUBLIC_SITE_URL || "http://localhost:3000";
const siteDescription =
  "Wandrix is a conversation-first AI travel planner with a live trip board and brochure-ready output.";

export const metadata: Metadata = {
  metadataBase: new URL(siteUrl),
  title: {
    default: "Wandrix",
    template: "%s | Wandrix",
  },
  description: siteDescription,
  openGraph: {
    title: "Wandrix",
    description: siteDescription,
    url: siteUrl,
    siteName: "Wandrix",
    images: [
      {
        url: "/images/homepage-hero-wandrix-v1.png",
        width: 1200,
        height: 900,
        alt: "Wandrix conversation-first travel planner workspace",
      },
    ],
    locale: "en_US",
    type: "website",
  },
  twitter: {
    card: "summary_large_image",
    title: "Wandrix",
    description: siteDescription,
    images: ["/images/homepage-hero-wandrix-v1.png"],
  },
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
      className={cn(
        "h-full",
        "antialiased",
        cormorant.variable,
        geistMono.variable,
        sora.variable,
        "font-sans",
        geist.variable,
      )}
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
