import Link from "next/link";

import { SignOutButton } from "@/components/auth/sign-out-button";
import { createClient as createSupabaseServerClient } from "@/lib/supabase/server";


export default async function Home() {
  const supabase = await createSupabaseServerClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  return (
    <main className="px-5 py-5 sm:px-8">
      <section className="grid min-h-[calc(100vh-7.5rem)] gap-5 lg:grid-cols-[1.2fr_0.8fr]">
        <div className="rounded-[2rem] border border-shell-border bg-shell p-8 shadow-[0_24px_80px_rgba(86,50,21,0.12)]">
          <div className="space-y-5">
            <span className="w-fit rounded-full border border-accent/20 bg-accent-soft px-3 py-1 text-xs font-semibold uppercase tracking-[0.22em] text-accent-strong">
              Conversation-first travel planning
            </span>
            <h1 className="max-w-4xl font-display text-6xl font-semibold tracking-tight text-foreground">
              Plan the trip in chat.
              <span className="block text-foreground/70">Watch the board build itself.</span>
            </h1>
            <p className="max-w-2xl text-lg leading-8 text-foreground/75">
              Wandrix is designed around a split workspace: chat on the left,
              live trip board on the right, and a brochure-quality outcome at the end.
            </p>
          </div>

          <div className="mt-8 flex flex-wrap gap-3">
            <Link
              href={user ? "/chat" : "/auth?next=/chat"}
              className="rounded-full bg-accent px-6 py-3 text-sm font-semibold text-white transition hover:bg-accent-strong"
            >
              {user ? "Open chat workspace" : "Sign in to start planning"}
            </Link>
            {!user && (
              <Link
                href="/auth"
                className="rounded-full border border-shell-border px-6 py-3 text-sm font-semibold text-foreground transition hover:bg-background"
              >
                Create account
              </Link>
            )}
          </div>

          <div className="mt-10 grid gap-4 md:grid-cols-3">
            {[
              "Top nav for Home, Flights, Hotels, and Chat",
              "Sidebar with recent sessions and saved trips",
              "Chat and trip board sharing the full workspace",
            ].map((item) => (
              <div
                key={item}
                className="rounded-[1.5rem] border border-shell-border bg-panel px-4 py-4 text-sm leading-7 text-foreground/75"
              >
                {item}
              </div>
            ))}
          </div>
        </div>

        <div className="grid gap-5">
          <div className="rounded-[2rem] border border-shell-border bg-shell p-6 shadow-[0_24px_80px_rgba(86,50,21,0.12)]">
            <p className="text-xs font-semibold uppercase tracking-[0.22em] text-accent-strong">
              Account
            </p>
            {user ? (
              <div className="mt-4 flex items-center justify-between gap-4 rounded-[1.5rem] border border-shell-border bg-panel px-4 py-4">
                <div>
                  <p className="font-semibold text-foreground">Signed in</p>
                  <p className="text-sm text-foreground/70">{user.email}</p>
                </div>
                <SignOutButton />
              </div>
            ) : (
              <div className="mt-4 rounded-[1.5rem] border border-shell-border bg-panel px-4 py-4 text-sm leading-7 text-foreground/75">
                Sign in before entering the planner so your conversation, board,
                and saved trips all stay attached to your account.
              </div>
            )}
          </div>

          <div className="rounded-[2rem] border border-shell-border bg-shell p-6 shadow-[0_24px_80px_rgba(86,50,21,0.12)]">
            <p className="text-xs font-semibold uppercase tracking-[0.22em] text-accent-strong">
              Product shape
            </p>
            <div className="mt-4 grid gap-3">
              {[
                "Chat route uses the full page instead of a centered card",
                "Recent sessions sit in the left sidebar",
                "Trip board stays visible while the conversation evolves",
                "Saved trips route is reserved for the library view",
              ].map((item) => (
                <div
                  key={item}
                  className="rounded-[1.25rem] border border-shell-border bg-panel px-4 py-3 text-sm leading-7 text-foreground/75"
                >
                  {item}
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>
    </main>
  );
}
