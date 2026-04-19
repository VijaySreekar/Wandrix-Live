import Link from "next/link";
import { ArrowRight, Calendar, MapPin, Sparkles } from "lucide-react";

import { BackgroundBeamsWithCollision } from "@/components/ui/background-beams-with-collision";
import { createClient as createSupabaseServerClient } from "@/lib/supabase/server";

export default async function Home() {
  const supabase = await createSupabaseServerClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  const primaryHref = user ? "/chat" : "/auth?next=/chat";
  const secondaryHref = user ? "/trips" : "/auth";

  return (
    <BackgroundBeamsWithCollision className="min-h-[calc(100vh-4rem)] py-16 md:py-24">
      <main className="relative z-10 mx-auto flex w-full max-w-6xl flex-col items-center px-4 sm:px-6">
        <div className="inline-flex items-center gap-2 rounded-full border border-border/50 bg-background/60 px-3 py-1 text-sm text-muted-foreground backdrop-blur">
          <Sparkles className="h-4 w-4 text-accent" />
          Agent-driven travel packages, end-to-end.
        </div>

        <h1 className="mt-6 max-w-3xl text-balance text-center [font-family:var(--font-brand)] text-4xl font-semibold leading-[1.05] tracking-tight sm:text-6xl">
          Plan trips in minutes with{" "}
          <span className="bg-[linear-gradient(135deg,var(--accent),var(--accent2))] bg-clip-text text-transparent">
            Wandrix
          </span>
          .
        </h1>

        <p className="mt-6 max-w-2xl text-pretty text-center text-lg leading-8 text-muted-foreground">
          Tell us your budget, dates, interests, accessibility needs, and
          weather preferences. Wandrix assembles a feasible itinerary with
          stays, transport, and activities, plus a clear price breakdown.
        </p>

        <div className="mt-8 flex flex-col items-center gap-3 sm:flex-row">
          <Link
            href={primaryHref}
            className="inline-flex h-11 items-center justify-center gap-2 rounded-full bg-[linear-gradient(135deg,var(--accent),var(--accent2))] px-6 text-accent-foreground shadow-sm transition hover:opacity-95"
          >
            Get Started <ArrowRight className="h-4 w-4" />
          </Link>
          <Link
            href={secondaryHref}
            className="inline-flex h-11 items-center justify-center rounded-full border border-border/60 bg-background px-6 text-foreground shadow-sm transition hover:bg-muted/40"
          >
            View dashboard
          </Link>
        </div>

        <section className="mt-12 grid w-full grid-cols-1 gap-4 md:grid-cols-3">
          <div className="rounded-2xl border border-border/60 bg-background/60 p-6 shadow-sm backdrop-blur">
            <div className="flex items-center gap-2 text-sm font-medium">
              <Calendar className="h-4 w-4 text-accent" />
              Constraints first
            </div>
            <p className="mt-3 text-sm leading-6 text-muted-foreground">
              Dates, budget, and time windows are treated as hard constraints.
              Itineraries are built to be feasible, not just pretty.
            </p>
          </div>

          <div className="rounded-2xl border border-border/60 bg-background/60 p-6 shadow-sm backdrop-blur">
            <div className="flex items-center gap-2 text-sm font-medium">
              <MapPin className="h-4 w-4 text-accent" />
              Places + activities
            </div>
            <p className="mt-3 text-sm leading-6 text-muted-foreground">
              Curated options based on interests, seasonality, and
              accessibility needs, organized day-by-day with trade-offs
              explained.
            </p>
          </div>

          <div className="rounded-2xl border border-border/60 bg-background/60 p-6 shadow-sm backdrop-blur">
            <div className="flex items-center gap-2 text-sm font-medium">
              <span className="h-4 w-4 rounded-full bg-[linear-gradient(135deg,var(--accent),var(--accent2))]" />
              Modular providers
            </div>
            <p className="mt-3 text-sm leading-6 text-muted-foreground">
              Built with a provider-agnostic API layer so services can be
              swapped without rewriting the planning logic.
            </p>
          </div>
        </section>
      </main>
    </BackgroundBeamsWithCollision>
  );
}
