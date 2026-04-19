import { redirect } from "next/navigation";

import { ProfilePageView } from "@/components/profile/profile-page";
import { createClient as createSupabaseServerClient } from "@/lib/supabase/server";

export default async function ProfilePage() {
  const supabase = await createSupabaseServerClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (!user) {
    redirect("/auth?next=/profile");
  }

  const userMetadata =
    user.user_metadata && typeof user.user_metadata === "object"
      ? (user.user_metadata as Record<string, unknown>)
      : {};

  const initialDisplayName =
    (typeof userMetadata.full_name === "string" && userMetadata.full_name) ||
    (typeof userMetadata.name === "string" && userMetadata.name) ||
    user.email?.split("@")[0] ||
    "Traveler";

  const avatarUrl =
    (typeof userMetadata.avatar_url === "string" && userMetadata.avatar_url) ||
    null;

  return (
    <main className="min-h-[calc(100vh-var(--nav-height))]">
      <ProfilePageView
        userId={user.id}
        initialEmail={user.email ?? ""}
        initialDisplayName={initialDisplayName}
        avatarUrl={avatarUrl}
      />
    </main>
  );
}
