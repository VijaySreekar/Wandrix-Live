"use client";

import { LogOut, UserRound } from "lucide-react";
import Image from "next/image";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useMemo, useState } from "react";

import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuGroup,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/animate-ui/components/radix/dropdown-menu";
import { createClient as createSupabaseBrowserClient } from "@/lib/supabase/client";
import { cn } from "@/lib/utils";

type UserAccountPopoverProps = {
  avatarUrl?: string | null;
  email: string;
  name: string;
};

export function UserAccountPopover({
  avatarUrl,
  email,
  name,
}: UserAccountPopoverProps) {
  const router = useRouter();
  const supabase = useMemo(() => createSupabaseBrowserClient(), []);
  const [isSigningOut, setIsSigningOut] = useState(false);

  const displayName = name.trim() || "Traveler";
  const initials = displayName
    .split(" ")
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase())
    .join("");

  async function handleSignOut() {
    setIsSigningOut(true);

    try {
      await supabase.auth.signOut();
      router.replace("/auth");
      router.refresh();
    } finally {
      setIsSigningOut(false);
    }
  }

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <button
          type="button"
          className="inline-flex items-center gap-2 rounded-full px-1 py-1 text-left transition-colors hover:bg-[color:var(--nav-hover)] focus:outline-none"
        >
          <AvatarChip
            avatarUrl={avatarUrl}
            initials={initials || "W"}
            name={displayName}
          />
          <div className="hidden min-w-0 pr-1 sm:block">
            <p className="max-w-40 truncate text-sm font-medium text-foreground">
              {displayName}
            </p>
          </div>
        </button>
      </DropdownMenuTrigger>

      <DropdownMenuContent
        side="bottom"
        align="end"
        className="w-64 border-[color:var(--nav-border)] bg-[color:var(--nav-shell)]"
      >
        <DropdownMenuLabel className="pb-1">
          <div className="flex items-center gap-3">
            <AvatarChip
              avatarUrl={avatarUrl}
              initials={initials || "W"}
              name={displayName}
              large
            />
            <div className="min-w-0">
              <p className="truncate text-sm font-medium text-foreground">
                {displayName}
              </p>
              <p className="truncate text-xs text-foreground/56">{email}</p>
            </div>
          </div>
        </DropdownMenuLabel>

        <DropdownMenuSeparator />

        <DropdownMenuGroup>
          <DropdownMenuItem asChild>
            <Link href="/profile" className="flex w-full items-center">
              <UserRound className="h-4 w-4" />
              Profile
            </Link>
          </DropdownMenuItem>
        </DropdownMenuGroup>

        <DropdownMenuSeparator />

        <DropdownMenuItem
          variant="destructive"
          onSelect={() => {
            void handleSignOut();
          }}
        >
          <LogOut className="h-4 w-4" />
          {isSigningOut ? "Signing out..." : "Sign out"}
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}

function AvatarChip({
  avatarUrl,
  initials,
  name,
  large = false,
}: {
  avatarUrl?: string | null;
  initials: string;
  name: string;
  large?: boolean;
}) {
  const size = large ? "h-10 w-10 text-sm" : "h-9 w-9 text-xs";

  if (avatarUrl) {
    return (
      <Image
        alt={name}
        src={avatarUrl}
        width={large ? 40 : 36}
        height={large ? 40 : 36}
        className={cn(
          "rounded-full border border-[color:var(--nav-utility-border)] object-cover",
          size,
        )}
      />
    );
  }

  return (
    <span
      style={{ backgroundImage: "var(--nav-avatar-bg)" }}
      className={cn(
        "inline-flex items-center justify-center rounded-full border border-white/40 font-medium text-[color:var(--nav-avatar-text)] shadow-sm",
        size,
      )}
    >
      {initials}
    </span>
  );
}
