import { redirect } from "next/navigation";

import { TravelPackageWorkspace } from "@/components/package/travel-package-workspace";
import { createClient as createSupabaseServerClient } from "@/lib/supabase/server";


export default async function ChatPage() {
  const supabase = await createSupabaseServerClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (!user) {
    redirect("/auth?next=/chat");
  }

  return (
    <main className="h-[calc(100vh-4.5rem)] px-3 pb-3 pt-3 sm:px-4 sm:pb-4 sm:pt-4">
      <TravelPackageWorkspace />
    </main>
  );
}
