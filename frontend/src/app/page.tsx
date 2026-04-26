import Image from "next/image";
import Link from "next/link";
import {
  ArrowRight,
  BookOpenText,
  CalendarDays,
  Compass,
  Hotel,
  LayoutPanelLeft,
  MapPinned,
  MessageSquareText,
  PlaneTakeoff,
  Route,
  ShieldCheck,
  Sparkles,
  Wallet,
  type LucideIcon,
} from "lucide-react";

import { createClient as createSupabaseServerClient } from "@/lib/supabase/server";

type Pillar = {
  title: string;
  description: string;
  icon: LucideIcon;
};

type JourneyStep = {
  eyebrow: string;
  title: string;
  description: string;
  imageSrc: string;
  imageAlt: string;
  imageClassName: string;
};

type SupportView = {
  title: string;
  description: string;
  detail: string;
  icon: LucideIcon;
};

const pillars: Pillar[] = [
  {
    title: "Conversation first",
    description:
      "Tell Wandrix what you want in plain language and refine the trip naturally instead of filling out a rigid planning flow.",
    icon: MessageSquareText,
  },
  {
    title: "Live trip board",
    description:
      "The board keeps dates, stays, activities, and route logic visible while the conversation keeps moving.",
    icon: LayoutPanelLeft,
  },
  {
    title: "Brochure-ready finish",
    description:
      "Once the trip feels right, the plan can become a polished output with the details intact.",
    icon: BookOpenText,
  },
];

const journeySteps: JourneyStep[] = [
  {
    eyebrow: "Step 1",
    title: "Start with a rough brief",
    description:
      "The first move is simple: explain the kind of trip you want, the timing, the pace, and the constraints that matter.",
    imageSrc: "/images/homepage/chat-suggestion-board-live.png",
    imageAlt: "Wandrix conversation workspace showing a user prompt and planning reply",
    imageClassName: "object-cover object-[18%_18%]",
  },
  {
    eyebrow: "Step 2",
    title: "See the board react",
    description:
      "Suggestions, route flow, and destination comparisons stay structured on the right so choices do not disappear into the chat history.",
    imageSrc: "/images/homepage/chat-suggestion-board-stitch-pass.png",
    imageAlt: "Wandrix board showing compared destination options and planning workspace",
    imageClassName: "object-cover object-[74%_12%]",
  },
  {
    eyebrow: "Step 3",
    title: "Finish with something usable",
    description:
      "The goal is not just a nice conversation. The goal is a trip you can review, trust, and turn into a brochure-style output.",
    imageSrc: "/images/homepage-hero-wandrix-v1.png",
    imageAlt: "Wandrix planning experience presented as a polished product scene",
    imageClassName: "object-cover object-center",
  },
];

const supportViews: SupportView[] = [
  {
    title: "Flights",
    description:
      "Dive into routing and timing when you want to pressure-test the travel days.",
    detail: "Routing, timing, and transfer practicality",
    icon: PlaneTakeoff,
  },
  {
    title: "Hotels",
    description:
      "Inspect stay options without losing the main trip thread or board context.",
    detail: "Shortlists, switches, and stay fit",
    icon: Hotel,
  },
  {
    title: "Activities",
    description:
      "Review highlights and trade-offs after the destination direction begins to settle.",
    detail: "Experiences, pacing, and day shape",
    icon: MapPinned,
  },
];

const starterBriefs = [
  "A warm four-night break in late May with sea views and a calm pace.",
  "A culture-first city trip with walkable neighborhoods and one standout hotel.",
  "A practical family escape with easy logistics, gentle weather, and room to slow down.",
  "A food-driven long weekend where flights stay reasonable and the route still feels elegant.",
];

export default async function Home() {
  const supabase = await createSupabaseServerClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  const primaryHref = user ? "/chat" : "/auth?next=/chat";
  const secondaryHref = user ? "/trips" : "#how-it-works";
  const secondaryLabel = user ? "Open saved trips" : "See how it works";

  return (
    <main className="overflow-hidden bg-background text-foreground">
      <section className="border-b border-[color:var(--nav-border)] bg-[color:var(--nav-shell)]">
        <div className="mx-auto max-w-[1480px] px-4 pb-18 pt-10 sm:px-6 lg:pb-24 lg:pt-14">
          <div className="grid gap-10 lg:grid-cols-[minmax(0,0.88fr)_minmax(0,1.12fr)] lg:items-center">
            <div className="relative max-w-2xl">
              <div
                className="pointer-events-none absolute -left-10 top-0 h-48 w-48 rounded-full blur-3xl"
                style={{
                  background:
                    "radial-gradient(circle, var(--accent-soft) 0%, transparent 72%)",
                }}
              />

              <span className="relative inline-flex min-h-10 items-center gap-2 rounded-full border border-[color:var(--nav-border)] bg-background/82 px-4 py-2 text-sm font-medium text-[color:var(--nav-brand-text)] backdrop-blur">
                <Sparkles className="h-4 w-4 text-accent" />
                Conversation-first AI travel planner
              </span>

              <h1 className="relative mt-6 max-w-[11ch] text-balance font-display text-5xl leading-none text-[color:var(--nav-brand-text)] sm:text-6xl lg:text-7xl">
                Plan in chat. Keep the trip visible.
              </h1>

              <p className="relative mt-6 max-w-[62ch] text-pretty text-lg leading-8 text-[color:var(--nav-link)]">
                Wandrix is built around the actual planning moment: you describe
                the trip, the live board takes shape beside the conversation,
                and the end state is a polished itinerary rather than a loose
                thread of ideas.
              </p>

              <div className="relative mt-8 flex flex-col gap-3 sm:flex-row">
                <Link
                  href={primaryHref}
                  className="inline-flex min-h-12 items-center justify-center gap-2 rounded-lg bg-[color:var(--accent)] px-5 py-3 text-sm font-semibold text-[color:var(--accent-foreground)] transition hover:bg-[color:var(--accent-strong)]"
                >
                  Start planning
                  <ArrowRight className="h-4 w-4" />
                </Link>
                <Link
                  href={secondaryHref}
                  className="inline-flex min-h-12 items-center justify-center gap-2 rounded-lg border border-[color:var(--nav-border)] bg-background/82 px-5 py-3 text-sm font-semibold text-[color:var(--nav-brand-text)] transition hover:bg-[color:var(--nav-hover)]"
                >
                  {secondaryLabel}
                </Link>
              </div>

              <dl className="relative mt-10 grid gap-4 sm:grid-cols-3">
                {pillars.map(({ title, description, icon: Icon }) => (
                  <div
                    key={title}
                    className="border-t border-[color:var(--nav-border-strong)] pt-4"
                  >
                    <dt className="flex items-center gap-2 text-sm font-semibold text-[color:var(--nav-brand-text)]">
                      <Icon className="h-4 w-4 text-accent" />
                      {title}
                    </dt>
                    <dd className="mt-2 text-sm leading-6 text-[color:var(--nav-link)]">
                      {description}
                    </dd>
                  </div>
                ))}
              </dl>
            </div>

            <div className="relative">
              <div
                className="pointer-events-none absolute inset-x-[14%] top-4 h-72 rounded-full blur-3xl"
                style={{
                  background:
                    "radial-gradient(circle, var(--accent-soft) 0%, transparent 72%)",
                }}
              />

              <div className="relative overflow-hidden rounded-lg border border-[color:var(--nav-border)] bg-[color:var(--panel-strong)] shadow-[0_30px_90px_-42px_rgba(92,72,46,0.3)]">
                <div className="flex items-center justify-between border-b border-[color:var(--nav-border)] bg-background/88 px-4 py-3 text-[13px] text-[color:var(--nav-link)]">
                  <div className="flex items-center gap-3">
                    <span className="h-2.5 w-2.5 rounded-full bg-[color:var(--accent)]" />
                    <span className="font-medium text-[color:var(--nav-brand-text)]">
                      One conversation, one trip board
                    </span>
                  </div>
                  <span className="hidden text-[12px] text-[color:var(--muted-foreground)] sm:inline">
                    Chat on the left, live board on the right
                  </span>
                </div>

                <div className="relative aspect-[16/10]">
                  <Image
                    src="/images/homepage/chat-suggestion-board-live.png"
                    alt="Wandrix workspace showing a conversation and destination suggestion board"
                    fill
                    priority
                    className="object-cover object-top"
                    sizes="(max-width: 1024px) 100vw, 58vw"
                  />
                </div>
              </div>

              <div className="mt-4 grid gap-3 sm:grid-cols-3">
                <div className="rounded-lg border border-[color:var(--nav-border)] bg-background/84 p-4">
                  <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-[color:var(--muted-foreground)]">
                    Prompt
                  </p>
                  <p className="mt-2 text-sm leading-6 text-[color:var(--nav-brand-text)]">
                    “I want somewhere sunny in March for a short break.”
                  </p>
                </div>
                <div className="rounded-lg border border-[color:var(--nav-border)] bg-background/84 p-4">
                  <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-[color:var(--muted-foreground)]">
                    Board
                  </p>
                  <p className="mt-2 text-sm leading-6 text-[color:var(--nav-brand-text)]">
                    Canary Islands, Malta, Madeira, and Seville stay visible as
                    practical options.
                  </p>
                </div>
                <div className="rounded-lg border border-[color:var(--nav-border)] bg-background/84 p-4">
                  <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-[color:var(--muted-foreground)]">
                    Outcome
                  </p>
                  <p className="mt-2 text-sm leading-6 text-[color:var(--nav-brand-text)]">
                    A route, stay decisions, and a cleaner trip package instead
                    of scattered notes.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section
        id="how-it-works"
        className="border-b border-[color:var(--nav-border)] bg-background"
      >
        <div className="mx-auto max-w-[1480px] px-4 py-16 sm:px-6 lg:py-20">
          <div className="max-w-3xl">
            <p className="text-sm font-semibold uppercase tracking-[0.18em] text-[color:var(--accent-strong)]">
              How it feels
            </p>
            <h2 className="mt-4 max-w-[14ch] text-balance font-display text-4xl leading-tight text-[color:var(--nav-brand-text)] sm:text-5xl">
              The homepage should show the product in motion.
            </h2>
            <p className="mt-4 max-w-[64ch] text-pretty text-base leading-7 text-[color:var(--nav-link)] sm:text-lg">
              Wandrix works best when the interaction is visible. A good
              homepage should make the planning rhythm obvious: brief in chat,
              compare in the board, then move toward a finished itinerary.
            </p>
          </div>

          <div className="mt-10 grid gap-6 lg:grid-cols-3">
            {journeySteps.map(
              ({ eyebrow, title, description, imageSrc, imageAlt, imageClassName }) => (
                <article
                  key={title}
                  className="overflow-hidden rounded-lg border border-[color:var(--nav-border)] bg-[color:var(--nav-shell)] shadow-[0_20px_60px_-44px_rgba(15,23,42,0.22)]"
                >
                  <div className="relative aspect-[16/11]">
                    <Image
                      src={imageSrc}
                      alt={imageAlt}
                      fill
                      className={imageClassName}
                      sizes="(max-width: 1024px) 100vw, 33vw"
                    />
                  </div>
                  <div className="p-6">
                    <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-[color:var(--accent-strong)]">
                      {eyebrow}
                    </p>
                    <h3 className="mt-3 text-2xl font-semibold text-[color:var(--nav-brand-text)]">
                      {title}
                    </h3>
                    <p className="mt-3 text-sm leading-6 text-[color:var(--nav-link)]">
                      {description}
                    </p>
                  </div>
                </article>
              ),
            )}
          </div>
        </div>
      </section>

      <section className="border-b border-[color:var(--nav-border)] bg-[color:var(--nav-shell-strong)]/52">
        <div className="mx-auto grid max-w-[1480px] gap-10 px-4 py-16 sm:px-6 lg:grid-cols-[minmax(0,0.82fr)_minmax(0,1.18fr)] lg:items-center lg:py-20">
          <div className="max-w-xl">
            <p className="text-sm font-semibold uppercase tracking-[0.18em] text-[color:var(--accent-strong)]">
              Live board
            </p>
            <h2 className="mt-4 text-balance font-display text-4xl leading-tight text-[color:var(--nav-brand-text)] sm:text-5xl">
              A clear trip board, not a buried summary.
            </h2>
            <p className="mt-4 text-pretty text-base leading-7 text-[color:var(--nav-link)] sm:text-lg">
              This is the real differentiator. The chat helps you think, but
              the structured draft keeps the trip legible: which destinations
              are in play, how the route flows, where the budget is leaning, and
              what still needs a decision.
            </p>

            <div className="mt-8 space-y-5">
              <div className="flex items-start gap-3">
                <div className="mt-1 flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-[color:var(--accent-soft)] text-[color:var(--accent-strong)]">
                  <CalendarDays className="h-5 w-5" />
                </div>
                <div>
                  <h3 className="text-base font-semibold text-[color:var(--nav-brand-text)]">
                    Real-world constraints stay visible
                  </h3>
                  <p className="mt-1 text-sm leading-6 text-[color:var(--nav-link)]">
                    Dates, pace, and practicality do not vanish behind the
                    assistant reply.
                  </p>
                </div>
              </div>
              <div className="flex items-start gap-3">
                <div className="mt-1 flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-[color:var(--accent-soft)] text-[color:var(--accent-strong)]">
                  <Route className="h-5 w-5" />
                </div>
                <div>
                  <h3 className="text-base font-semibold text-[color:var(--nav-brand-text)]">
                    Routing becomes part of the conversation
                  </h3>
                  <p className="mt-1 text-sm leading-6 text-[color:var(--nav-link)]">
                    Destination choices, stop order, and trip shape are refined
                    in the open instead of stitched together later.
                  </p>
                </div>
              </div>
              <div className="flex items-start gap-3">
                <div className="mt-1 flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-[color:var(--accent-soft)] text-[color:var(--accent-strong)]">
                  <Wallet className="h-5 w-5" />
                </div>
                <div>
                  <h3 className="text-base font-semibold text-[color:var(--nav-brand-text)]">
                    Budget clarity stays in frame
                  </h3>
                  <p className="mt-1 text-sm leading-6 text-[color:var(--nav-link)]">
                    Costs feel easier to reason about when the board owns the
                    structure instead of the chat trying to remember everything.
                  </p>
                </div>
              </div>
            </div>
          </div>

          <div className="overflow-hidden rounded-lg border border-[color:var(--nav-border)] bg-background shadow-[0_28px_80px_-42px_rgba(15,23,42,0.24)]">
            <div className="flex items-center justify-between border-b border-[color:var(--nav-border)] bg-[color:var(--nav-shell)] px-4 py-3 text-sm text-[color:var(--nav-link)]">
              <span className="font-medium text-[color:var(--nav-brand-text)]">
                Product snapshot
              </span>
              <span className="text-[12px] text-[color:var(--muted-foreground)]">
                Conversation and board working together
              </span>
            </div>
            <div className="relative aspect-[16/9]">
              <Image
                src="/images/homepage/chat-suggestion-board-stitch-pass.png"
                alt="Wandrix product view showing the conversation area and destination board together"
                fill
                className="object-cover object-top"
                sizes="(max-width: 1024px) 100vw, 56vw"
              />
            </div>
          </div>
        </div>
      </section>

      <section className="border-b border-[color:var(--nav-border)] bg-background">
        <div className="mx-auto max-w-[1480px] px-4 py-16 sm:px-6 lg:py-20">
          <div className="grid gap-10 lg:grid-cols-[minmax(0,0.86fr)_minmax(0,1.14fr)] lg:items-start">
            <div className="max-w-xl">
              <p className="text-sm font-semibold uppercase tracking-[0.18em] text-[color:var(--accent-strong)]">
                Supporting views
              </p>
              <h2 className="mt-4 text-balance font-display text-4xl leading-tight text-[color:var(--nav-brand-text)] sm:text-5xl">
                Specialist views when you need a closer look.
              </h2>
              <p className="mt-4 text-pretty text-base leading-7 text-[color:var(--nav-link)] sm:text-lg">
                Flights, hotels, and activities should feel like focused lenses
                on the same trip, not separate products pulling attention away
                from the main planning thread.
              </p>
              <div className="mt-8 flex flex-wrap gap-3 text-sm text-[color:var(--nav-brand-text)]">
                <span className="inline-flex items-center gap-2 rounded-full border border-[color:var(--nav-border)] px-3 py-1.5">
                  <ShieldCheck className="h-4 w-4 text-accent" />
                  One trip context
                </span>
                <span className="inline-flex items-center gap-2 rounded-full border border-[color:var(--nav-border)] px-3 py-1.5">
                  <ShieldCheck className="h-4 w-4 text-accent" />
                  Shared draft ownership
                </span>
                <span className="inline-flex items-center gap-2 rounded-full border border-[color:var(--nav-border)] px-3 py-1.5">
                  <ShieldCheck className="h-4 w-4 text-accent" />
                  Return to chat naturally
                </span>
              </div>
            </div>

            <div className="grid gap-4 md:grid-cols-3">
              {supportViews.map(({ title, description, detail, icon: Icon }) => (
                <article
                  key={title}
                  className="overflow-hidden rounded-lg border border-[color:var(--nav-border)] bg-[color:var(--nav-shell)] shadow-[0_18px_50px_-40px_rgba(15,23,42,0.18)]"
                >
                  <div className="relative aspect-[16/10] border-b border-[color:var(--nav-border)] bg-[linear-gradient(180deg,rgba(255,255,255,0.42),rgba(255,255,255,0.04))]">
                    <div className="absolute inset-0">
                      <Image
                        src="/images/homepage/chat-suggestion-board-live.png"
                        alt=""
                        fill
                        aria-hidden
                        className="object-cover object-[72%_18%] opacity-88"
                        sizes="(max-width: 768px) 100vw, 24vw"
                      />
                    </div>
                    <div className="absolute inset-x-4 top-4 flex items-center justify-between rounded-lg border border-white/70 bg-background/88 px-3 py-2 backdrop-blur">
                      <div className="flex items-center gap-2">
                        <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-[color:var(--accent-soft)] text-[color:var(--accent-strong)]">
                          <Icon className="h-4 w-4" />
                        </div>
                        <span className="text-sm font-semibold text-[color:var(--nav-brand-text)]">
                          {title}
                        </span>
                      </div>
                    </div>
                    <div className="absolute bottom-4 left-4 right-4 rounded-lg border border-white/70 bg-background/90 p-3 backdrop-blur">
                      <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-[color:var(--muted-foreground)]">
                        Focus
                      </p>
                      <p className="mt-2 text-sm leading-6 text-[color:var(--nav-brand-text)]">
                        {detail}
                      </p>
                    </div>
                  </div>
                  <div className="p-5">
                    <h3 className="text-lg font-semibold text-[color:var(--nav-brand-text)]">
                      {title}
                    </h3>
                    <p className="mt-2 text-sm leading-6 text-[color:var(--nav-link)]">
                      {description}
                    </p>
                  </div>
                </article>
              ))}
            </div>
          </div>
        </div>
      </section>

      <section className="bg-[color:var(--nav-shell)]">
        <div className="mx-auto max-w-[1480px] px-4 py-16 sm:px-6 lg:py-20">
          <div className="grid gap-10 lg:grid-cols-[minmax(0,0.82fr)_minmax(0,1.18fr)] lg:items-center">
            <div className="max-w-xl">
              <p className="text-sm font-semibold uppercase tracking-[0.18em] text-[color:var(--accent-strong)]">
                Try a brief
              </p>
              <h2 className="mt-4 text-balance font-display text-4xl leading-tight text-[color:var(--nav-brand-text)] sm:text-5xl">
                Start with a sentence that sounds like a real traveler.
              </h2>
              <p className="mt-4 text-pretty text-base leading-7 text-[color:var(--nav-link)] sm:text-lg">
                A better close is not another vague slogan. It is helping people
                imagine the first thing they would actually type into the
                planner.
              </p>

              <div className="mt-8 flex flex-col gap-3 sm:flex-row">
                <Link
                  href={primaryHref}
                  className="inline-flex min-h-12 items-center justify-center gap-2 rounded-lg bg-[color:var(--accent)] px-5 py-3 text-sm font-semibold text-[color:var(--accent-foreground)] transition hover:bg-[color:var(--accent-strong)]"
                >
                  Open the planner
                  <ArrowRight className="h-4 w-4" />
                </Link>
                <Link
                  href="/chat"
                  className="inline-flex min-h-12 items-center justify-center gap-2 rounded-lg border border-[color:var(--nav-border)] bg-background/84 px-5 py-3 text-sm font-semibold text-[color:var(--nav-brand-text)] transition hover:bg-[color:var(--nav-hover)]"
                >
                  See the workspace
                </Link>
              </div>
            </div>

            <div className="grid gap-3 sm:grid-cols-2">
              {starterBriefs.map((brief) => (
                <div
                  key={brief}
                  className="rounded-lg border border-[color:var(--nav-border)] bg-background/88 p-5 shadow-[0_18px_50px_-40px_rgba(15,23,42,0.18)]"
                >
                  <div className="flex items-center gap-2 text-[11px] font-semibold uppercase tracking-[0.18em] text-[color:var(--muted-foreground)]">
                    <Compass className="h-4 w-4 text-accent" />
                    Starter brief
                  </div>
                  <p className="mt-3 text-sm leading-6 text-[color:var(--nav-brand-text)]">
                    “{brief}”
                  </p>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>
    </main>
  );
}
