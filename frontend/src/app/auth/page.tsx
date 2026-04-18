import { redirect } from "next/navigation";

import { AuthShell } from "@/components/auth/auth-shell";
import { createClient as createSupabaseServerClient } from "@/lib/supabase/server";


type AuthPageProps = {
  searchParams: Promise<{
    next?: string;
  }>;
};


export default async function AuthPage({ searchParams }: AuthPageProps) {
  const params = await searchParams;
  const nextPath =
    params.next && params.next.startsWith("/") ? params.next : "/chat";

  const supabase = await createSupabaseServerClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (user) {
    redirect(nextPath);
  }

  return <AuthShell nextPath={nextPath} />;
}
