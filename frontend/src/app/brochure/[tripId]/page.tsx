import { redirect } from "next/navigation";

import { TripBrochure } from "@/components/brochure/trip-brochure";
import { createClient as createSupabaseServerClient } from "@/lib/supabase/server";

type BrochurePageProps = {
  params: Promise<{
    tripId: string;
  }>;
};

export default async function BrochurePage({ params }: BrochurePageProps) {
  const supabase = await createSupabaseServerClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (!user) {
    redirect("/auth?next=/trips");
  }

  const resolvedParams = await params;

  return (
    <main className="min-h-[calc(100vh-4.5rem)] px-3 pb-3 pt-3 sm:px-4 sm:pb-4 sm:pt-4">
      <TripBrochure tripId={resolvedParams.tripId} />
    </main>
  );
}
