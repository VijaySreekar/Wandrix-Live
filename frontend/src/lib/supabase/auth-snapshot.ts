"use client";

import type { Session } from "@supabase/supabase-js";

export type BrowserAuthSnapshot = {
  accessToken: string;
  userId: string;
  userMetadata: Record<string, unknown>;
};

export function toBrowserAuthSnapshot(
  session: Session | null | undefined,
): BrowserAuthSnapshot | null {
  if (!session?.access_token || !session.user?.id) {
    return null;
  }

  return {
    accessToken: session.access_token,
    userId: session.user.id,
    userMetadata:
      session.user.user_metadata &&
      typeof session.user.user_metadata === "object"
        ? (session.user.user_metadata as Record<string, unknown>)
        : {},
  };
}
