import { redirect } from "next/navigation";

import { TripModuleWorkspace } from "@/components/modules/trip-module-workspace";
import { createClient as createSupabaseServerClient } from "@/lib/supabase/server";

type ActivitiesPageProps = {
  searchParams?: Promise<{
    trip?: string;
  }>;
};

export default async function ActivitiesPage({
  searchParams,
}: ActivitiesPageProps) {
  const supabase = await createSupabaseServerClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (!user) {
    redirect("/auth?next=/activities");
  }

  const resolvedSearchParams = searchParams ? await searchParams : undefined;

  return (
    <main className="min-h-[calc(100vh-4.5rem)] px-3 pb-3 pt-3 sm:px-4 sm:pb-4 sm:pt-4">
      <TripModuleWorkspace
        module="activities"
        initialTripId={resolvedSearchParams?.trip}
      />
    </main>
  );
}
