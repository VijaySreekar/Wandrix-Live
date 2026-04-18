import Link from "next/link";

import { SignOutButton } from "@/components/auth/sign-out-button";
import { createClient as createSupabaseServerClient } from "@/lib/supabase/server";


const NAV_ITEMS = [
  { label: "Home", href: "/" },
  { label: "Flights", href: "/flights" },
  { label: "Hotels", href: "/hotels" },
  { label: "Activities", href: "/activities" },
  { label: "Chat", href: "/chat" },
];


export async function AppTopNav() {
  const supabase = await createSupabaseServerClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();
  const navItems = user
    ? NAV_ITEMS
    : [...NAV_ITEMS, { label: "Login", href: "/auth?next=/chat" }];

  return (
    <header className="sticky top-0 z-50 border-b border-shell-border bg-shell/95">
      <div className="flex h-[4.5rem] w-full items-center justify-between gap-6 px-4 sm:px-6 lg:px-8">
        <div className="flex min-w-0 items-center gap-8">
          <Link className="font-display text-3xl font-semibold tracking-tight text-foreground" href="/">
            Wandrix
          </Link>
          <nav className="hidden items-center gap-1 md:flex">
            {navItems.map((item) => (
              <Link
                key={item.href}
                href={item.href}
                className="rounded-md px-3 py-2 text-sm font-medium text-foreground/68 transition-colors hover:bg-panel hover:text-foreground"
              >
                {item.label}
              </Link>
            ))}
          </nav>
        </div>

        <div className="flex items-center gap-3">
          {user ? (
            <>
              <div className="hidden rounded-md border border-shell-border bg-panel px-3 py-2 text-sm text-foreground/70 sm:block">
                {user.email}
              </div>
              <SignOutButton />
            </>
          ) : null}
        </div>
      </div>
    </header>
  );
}
