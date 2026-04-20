import { redirect } from "next/navigation";

import { ProviderUsagePage } from "@/components/providers/provider-usage-page";
import { createClient as createSupabaseServerClient } from "@/lib/supabase/server";


export default async function ProvidersPage() {
  const supabase = await createSupabaseServerClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (!user) {
    redirect("/auth?next=/providers");
  }

  return (
    <main className="min-h-[calc(100vh-4.5rem)] px-3 pb-4 pt-4 sm:px-4">
      <ProviderUsagePage />
    </main>
  );
}
