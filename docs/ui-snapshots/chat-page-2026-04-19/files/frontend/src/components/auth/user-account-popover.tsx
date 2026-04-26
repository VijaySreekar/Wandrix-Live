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
          className="inline-flex items-center gap-3 rounded-lg border border-transparent bg-transparent px-2 py-1.5 text-left transition-colors hover:border-shell-border/80 hover:bg-[color:var(--nav-surface-strong)] focus:outline-none"
        >
          <AvatarChip
            avatarUrl={avatarUrl}
            initials={initials || "W"}
            name={displayName}
          />
          <div className="hidden min-w-0 sm:block">
            <p className="max-w-44 truncate text-sm font-medium text-foreground">
              {displayName}
            </p>
          </div>
        </button>
      </DropdownMenuTrigger>

      <DropdownMenuContent side="bottom" align="start" className="w-64">
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
        className={cn("rounded-full object-cover", size)}
      />
    );
  }

  return (
    <span
      className={cn(
        "inline-flex items-center justify-center rounded-full bg-[linear-gradient(135deg,var(--accent),var(--accent2))] font-medium text-accent-foreground",
        size,
      )}
    >
      {initials}
    </span>
  );
}
