import Link from "next/link";

import { AppNavLinks } from "@/components/app/app-nav-links";
import { BrandWordmark } from "@/components/app/brand-wordmark";
import { UserAccountPopover } from "@/components/auth/user-account-popover";
import { AccentPicker } from "@/components/ui/accent-picker";
import { ThemeToggle } from "@/components/ui/theme-toggle";
import { createClient as createSupabaseServerClient } from "@/lib/supabase/server";


const NAV_ITEMS = [
  { label: "Home", href: "/" },
  { label: "Chat", href: "/chat" },
  { label: "Saved Trips", href: "/trips" },
  { label: "Flights", href: "/flights" },
  { label: "Hotels", href: "/hotels" },
  { label: "Activities", href: "/activities" },
];


export async function AppTopNav() {
  const supabase = await createSupabaseServerClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();
  const userMetadata =
    user?.user_metadata && typeof user.user_metadata === "object"
      ? (user.user_metadata as Record<string, unknown>)
      : {};
  const displayName =
    (typeof userMetadata.full_name === "string" && userMetadata.full_name) ||
    (typeof userMetadata.name === "string" && userMetadata.name) ||
    user?.email?.split("@")[0] ||
    "Traveler";
  const avatarUrl =
    (typeof userMetadata.avatar_url === "string" && userMetadata.avatar_url) ||
    null;

  return (
    <header className="sticky top-0 z-50 border-b border-shell-border/80 bg-[color:var(--nav-surface)]/95 backdrop-blur supports-[backdrop-filter]:bg-[color:var(--nav-surface)]/88">
      <div className="mx-auto flex h-[var(--nav-height)] max-w-[1600px] items-center justify-between gap-4 px-4 sm:px-6">
        <div className="flex min-w-0 items-center gap-3">
          <Link
            href="/"
            className="flex h-[2.75rem] items-center rounded-md px-2 transition-opacity hover:opacity-90"
          >
            <BrandWordmark />
          </Link>
          <AppNavLinks items={NAV_ITEMS} />
        </div>

        <div className="flex items-center gap-3">
          {user ? (
            <UserAccountPopover
              avatarUrl={avatarUrl}
              email={user.email ?? ""}
              name={displayName}
            />
          ) : (
            <Link
              href="/auth?next=/chat"
              className="inline-flex items-center rounded-full bg-[linear-gradient(135deg,var(--accent),var(--accent2))] px-5 py-2.5 text-sm font-semibold text-accent-foreground shadow-sm transition hover:opacity-95"
            >
              Log in
            </Link>
          )}

          <div className="ml-1 flex items-center gap-1">
            <AccentPicker />
            <ThemeToggle />
          </div>
        </div>
      </div>

      <div className="border-t border-shell-border/50 px-4 py-2 lg:hidden">
        <AppNavLinks items={NAV_ITEMS} mobile />
      </div>
    </header>
  );
}
