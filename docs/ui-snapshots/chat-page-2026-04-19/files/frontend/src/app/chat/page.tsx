import { redirect } from "next/navigation";

import { TravelPackageWorkspace } from "@/components/package/travel-package-workspace";
import { OnboardingDialog } from "@/components/profile/onboarding-dialog";
import { createClient as createSupabaseServerClient } from "@/lib/supabase/server";


export default async function ChatPage() {
  const supabase = await createSupabaseServerClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (!user) {
    redirect("/auth?next=/chat");
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

  return (
    <main className="chat-workspace-shell h-[calc(100vh-4.75rem)] overflow-hidden">
      <TravelPackageWorkspace />
      <OnboardingDialog
        userId={user.id}
        initialEmail={user.email ?? ""}
        initialDisplayName={initialDisplayName}
      />
    </main>
  );
}
