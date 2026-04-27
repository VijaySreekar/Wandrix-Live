import { redirect } from "next/navigation";

import { TripLibrary } from "@/components/trips/trip-library";
import { createClient as createSupabaseServerClient } from "@/lib/supabase/server";

export default async function TripsPage() {
  const supabase = await createSupabaseServerClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (!user) {
    redirect("/auth?next=/trips");
  }

  return (
    <main className="min-h-[calc(100vh-4.5rem)] px-3 pb-3 pt-3 sm:px-4 sm:pb-4 sm:pt-4">
      <TripLibrary />
    </main>
  );
}
