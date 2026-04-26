import Link from "next/link";

import { AppNavLinks } from "@/components/app/app-nav-links";
import { BrandWordmark } from "@/components/app/brand-wordmark";
import { UserAccountPopover } from "@/components/auth/user-account-popover";
import { AccentPicker } from "@/components/ui/accent-picker";
import { ThemeToggle } from "@/components/ui/theme-toggle";
import { createClient as createSupabaseServerClient } from "@/lib/supabase/server";


const NAV_ITEMS = [
  { label: "Home", href: "/" },
  { label: "Chat", href: "/chat/new" },
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
    <header className="sticky top-0 z-50 border-b border-[color:var(--nav-border)] bg-[color:var(--nav-shell)]/95 backdrop-blur-xl">
      <div className="mx-auto max-w-[1680px] px-4 sm:px-6">
        <div className="flex min-h-[var(--nav-height)] items-center justify-between gap-4">
          <div className="flex min-w-0 items-center gap-4 sm:gap-6">
            <Link
              href="/"
              className="flex min-w-0 items-center rounded-full px-1 py-1 transition-opacity hover:opacity-92"
            >
              <BrandWordmark />
            </Link>

            <AppNavLinks items={NAV_ITEMS} />
          </div>

          <div className="flex shrink-0 items-center gap-1 sm:gap-2">
            <AccentPicker />
            <ThemeToggle />
            <div className="mx-1 hidden h-7 w-px bg-[color:var(--nav-divider)] sm:block" />
            {user ? (
              <UserAccountPopover
                avatarUrl={avatarUrl}
                email={user.email ?? ""}
                name={displayName}
              />
            ) : (
              <Link
                href="/auth?next=/chat/new"
                className="inline-flex min-h-11 items-center rounded-full px-4 py-2 text-sm font-medium text-[color:var(--nav-login-text)] transition-colors hover:bg-[color:var(--nav-hover)]"
              >
                Log in
              </Link>
            )}
          </div>
        </div>

        <div className="border-t border-[color:var(--nav-divider)] py-2 lg:hidden">
          <div className="flex items-center justify-between gap-3">
            <AppNavLinks items={NAV_ITEMS} mobile />
          </div>
        </div>
      </div>
    </header>
  );
}
