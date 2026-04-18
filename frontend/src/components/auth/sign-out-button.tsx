"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { createClient as createSupabaseBrowserClient } from "@/lib/supabase/client";


export function SignOutButton() {
  const router = useRouter();
  const [isLoading, setIsLoading] = useState(false);

  async function handleSignOut() {
    setIsLoading(true);

    try {
      const supabase = createSupabaseBrowserClient();
      await supabase.auth.signOut();
      router.replace("/auth");
      router.refresh();
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <button
      type="button"
      onClick={handleSignOut}
      disabled={isLoading}
      className="rounded-md border border-panel-border px-3 py-2 text-sm font-medium text-foreground transition-colors hover:bg-background disabled:cursor-not-allowed disabled:opacity-70"
    >
      {isLoading ? "Signing out..." : "Sign out"}
    </button>
  );
}
