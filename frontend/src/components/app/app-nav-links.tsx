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
          ? "mx-auto flex w-full max-w-[1600px] items-center gap-1 overflow-x-auto pb-1"
          : "hidden items-center gap-1 lg:flex"
      }
    >
      {items.map((item) => {
        const isActive =
          pathname === item.href ||
          ((item.href === "/chat" || item.href === "/chat/new") &&
            pathname.startsWith("/chat")) ||
          (item.href === "/trips" &&
            (pathname.startsWith("/trips") || pathname.startsWith("/brochure")));

        return (
          <Link
            key={item.href}
            href={item.href}
            aria-current={isActive ? "page" : undefined}
            className={[
              "inline-flex shrink-0 items-center justify-center rounded-full text-[0.98rem] font-medium transition-all duration-200",
              mobile
                ? "min-h-10 whitespace-nowrap px-4 py-2"
                : "min-h-11 px-5 py-2.5",
              "text-[color:var(--nav-link)] hover:bg-[color:var(--nav-hover)] hover:text-foreground",
              isActive
                ? "bg-[color:var(--nav-active-bg)] text-[color:var(--nav-active-text)] shadow-[var(--nav-active-shadow)]"
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
