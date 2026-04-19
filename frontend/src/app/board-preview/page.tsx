import { redirect } from "next/navigation";

import { TripBoardSandbox } from "@/components/package/trip-board-sandbox";
import { createClient as createSupabaseServerClient } from "@/lib/supabase/server";

export default async function BoardPreviewPage() {
  const supabase = await createSupabaseServerClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (!user) {
    redirect("/auth?next=/board-preview");
  }

  return <TripBoardSandbox />;
}
