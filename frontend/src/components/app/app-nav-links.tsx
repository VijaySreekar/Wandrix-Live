"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

type NavItem = {
  href: string;
  label: string;
};

type AppNavLinksProps = {
  items: NavItem[];
  mobile?: boolean;
};

export function AppNavLinks({
  items,
  mobile = false,
}: AppNavLinksProps) {
  const pathname = usePathname();

  return (
    <nav
      aria-label="Primary"
      className={
        mobile
          ? "mx-auto flex max-w-[1600px] items-center gap-1 overflow-x-auto"
          : "hidden items-center gap-1 rounded-full bg-transparent p-1 lg:flex"
      }
    >
      {items.map((item) => {
        const isActive =
          pathname === item.href ||
          (item.href === "/chat" && pathname.startsWith("/chat")) ||
          (item.href === "/trips" &&
            (pathname.startsWith("/trips") || pathname.startsWith("/brochure")));

        return (
          <Link
            key={item.href}
            href={item.href}
            aria-current={isActive ? "page" : undefined}
            className={[
              "relative rounded-xl px-3.5 py-2.5 text-[length:var(--nav-link-size)] font-medium transition-colors",
              mobile
                ? "whitespace-nowrap"
                : "",
              "text-muted hover:bg-background/70 hover:text-foreground lg:text-foreground/72 lg:hover:bg-foreground/[0.05] lg:hover:text-foreground",
              isActive
                ? "bg-background text-foreground shadow-sm lg:bg-foreground/[0.06] lg:shadow-none"
                : "",
            ]
              .filter(Boolean)
              .join(" ")}
          >
            {item.label}
          </Link>
        );
      })}
    </nav>
  );
}
