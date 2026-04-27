
import Link from "next/link";
import {
  ArrowRight,
  ArrowUpRight,
  BookOpenText,
  Clock,
  CloudSun,
  Compass,
  GitBranch,
  Hotel,
  Layers,
  MapPinned,
  Plane,
  ShieldCheck,
  Sparkles,
  Sun,
  Utensils,
  Waves,
} from "lucide-react";

import { createClient as createSupabaseServerClient } from "@/lib/supabase/server";

/* =====================================================================
 * Real product anchors used to shape this page (from the planner code):
 *  - destination shortlists with practicality_label, fit_label, tradeoffs,
 *    recommendation_note, "Recommended" badge, suggested / leading / confirmed
 *  - trip style: direction (primary + accent), pace, tradeoff axes
 *  - flight strategies: Direct, One-stop saver, Keep flexible
 *  - hotel workspace: max nightly rate, area, style, sort order
 *  - activities: essential / maybe / passed, scheduled by daypart
 *  - weather influence on day shape, conflict tracking, brochure export
 * ===================================================================== */

type Scenario = {
  tag: string;
  title: string;
  brief: string;
  meta: string;
  tone: "ocean" | "ember" | "sage" | "sand" | "ink" | "rose";
};

const scenarios: Scenario[] = [
  {
    tag: "Slow weekend",
    title: "Lisbon, off-script",
    brief:
      "Three nights, late May. Tile-cool mornings, a long lunch in Alfama, one extravagant rooftop dinner. No museums I'll regret skipping.",
    meta: "3 nights · ~£640pp · sea-view stay",
    tone: "ocean",
  },
  {
    tag: "Family pace",
    title: "Sicily, but easy",
    brief:
      "Two adults, two kids, last week of August. One base, lazy beach mornings, a Mount Etna day if it isn't a chore.",
    meta: "7 nights · 1 base · short transfers",
    tone: "ember",
  },
  {
    tag: "Culture-first",
    title: "Kyoto in shoulder season",
    brief:
      "Late October, eight days, walkable neighbourhoods. One ryokan splurge, the rest small inns. Skip the obvious tourist loops.",
    meta: "8 nights · 2 cities · rail-friendly",
    tone: "sage",
  },
  {
    tag: "Long weekend",
    title: "A food trip to Bologna",
    brief:
      "Friday to Monday. Direct flights only. One pasta-making class. Wine bar dinner over a tasting menu, every time.",
    meta: "3 nights · direct flights · trattoria-led",
    tone: "sand",
  },
  {
    tag: "Reset",
    title: "A quiet week in Madeira",
    brief:
      "Six nights in February. A walk that ends in a cafe. Levada trails I won't fall off. One driver day around the north coast.",
    meta: "6 nights · gentle pace · car for one day",
    tone: "ink",
  },
  {
    tag: "Honeymoon",
    title: "Amalfi without the queue",
    brief:
      "Ten nights in early June. A small Praiano hotel, a few Capri evenings, one Naples bookend. No cruise-port mornings.",
    meta: "10 nights · 3 stays · boat transfers",
    tone: "rose",
  },
];

const toneStyles: Record<Scenario["tone"], { bg: string; chip: string; accent: string }> = {
  ocean: {
    bg: "linear-gradient(160deg, #eef5f3 0%, #dceae5 100%)",
    chip: "rgba(22, 105, 94, 0.12)",
    accent: "#16695e",
  },
  ember: {
    bg: "linear-gradient(160deg, #fbeee2 0%, #f3d6bc 100%)",
    chip: "rgba(176, 92, 44, 0.14)",
    accent: "#a4541f",
  },
  sage: {
    bg: "linear-gradient(160deg, #eef1e7 0%, #dde3cd 100%)",
    chip: "rgba(76, 96, 53, 0.14)",
    accent: "#4a5e34",
  },
  sand: {
    bg: "linear-gradient(160deg, #faf3e2 0%, #f0e2bd 100%)",
    chip: "rgba(140, 105, 38, 0.16)",
    accent: "#7a5a1d",
  },
  ink: {
    bg: "linear-gradient(160deg, #e9ecef 0%, #cfd5db 100%)",
    chip: "rgba(40, 56, 74, 0.14)",
    accent: "#2a3a4d",
  },
  rose: {
    bg: "linear-gradient(160deg, #f6e7e3 0%, #ecccc4 100%)",
    chip: "rgba(150, 64, 70, 0.14)",
    accent: "#8d3a40",
  },
};

const marqueePhrases = [
  "Destination shortlists",
  "Day-shape over checklists",
  "Mediterranean cliffs",
  "Tradeoffs, not pitches",
  "Lisbon trams",
  "Direct vs. one-stop",
  "Norwegian fjords",
  "Brochure-ready output",
  "Kyoto laneways",
  "One base, short transfers",
  "Cycladic whitewash",
  "Pace before pins",
];

const faqs = [
  {
    q: "What does Wandrix actually do?",
    a: "It turns a conversation into a structured trip plan. You describe what you want; the planner builds a board on the right with destinations, dates, a route, days with morning/afternoon/evening shape, stays, flights and a budget &mdash; then exports it as a brochure-style document.",
  },
  {
    q: "How is this different from asking ChatGPT?",
    a: "A trip is a hundred small decisions that have to stay in view. Wandrix keeps the structured plan beside the chat, so dates, route, stays and budget don't get lost in scrollback. Every shortlist explains its working, with explicit tradeoffs and a 'recommended' option.",
  },
  {
    q: "Does it book the trip?",
    a: "Not directly. Wandrix is the planner: it builds a working itinerary you can keep, share, or hand to whoever does the booking. Stays and flights are presented as decisions on the board, not affiliate widgets.",
  },
  {
    q: "Can I change my mind halfway through?",
    a: "Yes &mdash; that&rsquo;s the point. Swap a destination, change pace, drop an activity, raise the budget. The board re-stitches and tells you what knocked into what. The chat keeps moving.",
  },
  {
    q: "What do I get at the end?",
    a: "A brochure: a polished, multi-page itinerary with the route, day-by-day plan, stays, and the things you said you cared about. It&rsquo;s a real document &mdash; not a chat transcript.",
  },
];

export default async function Home() {
  const supabase = await createSupabaseServerClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  const primaryHref = user ? "/chat" : "/auth?next=/chat";
  const secondaryHref = "#how";

  return (
    <main className="overflow-hidden bg-[color:var(--nav-shell)] text-[color:var(--nav-brand-text)]">
      {/* ============== HERO ============== */}
      <section className="relative border-b border-[color:var(--nav-border)]">
        <div
          aria-hidden
          className="pointer-events-none absolute inset-0 wx-grain opacity-60"
        />
        <div
          aria-hidden
          className="pointer-events-none absolute -left-32 top-10 h-[28rem] w-[28rem] rounded-full blur-3xl"
          style={{
            background:
              "radial-gradient(circle, rgba(22,105,94,0.18) 0%, transparent 65%)",
          }}
        />
        <div
          aria-hidden
          className="pointer-events-none absolute right-[-8rem] bottom-[-6rem] h-[26rem] w-[26rem] rounded-full blur-3xl"
          style={{
            background:
              "radial-gradient(circle, rgba(196,140,80,0.22) 0%, transparent 65%)",
          }}
        />

        <div className="relative mx-auto grid max-w-[1480px] gap-14 px-4 pb-20 pt-14 sm:px-6 lg:grid-cols-[minmax(0,0.9fr)_minmax(0,1.1fr)] lg:items-center lg:gap-12 lg:pb-28 lg:pt-20">
          {/* Left: editorial copy */}
          <div className="relative max-w-2xl wx-fade-up">
            <span className="inline-flex items-center gap-2 rounded-full border border-[color:var(--nav-border)] bg-background/70 px-3 py-1.5 text-[12px] font-medium tracking-wide text-[color:var(--nav-link)] backdrop-blur">
              <Compass className="h-3.5 w-3.5 text-[color:var(--accent)]" />
              A conversation-first travel planner
            </span>

            <h1 className="mt-7 font-display text-[3.4rem] leading-[1.02] tracking-tight text-[color:var(--nav-brand-text)] sm:text-[4.4rem] lg:text-[5.2rem]">
              Plan trips like
              <br />
              you&rsquo;re{" "}
              <span className="relative inline-block italic">
                thinking out loud
                <svg
                  aria-hidden
                  viewBox="0 0 320 18"
                  className="absolute -bottom-2 left-0 h-3 w-full"
                  preserveAspectRatio="none"
                >
                  <path
                    d="M2 12 C 60 2, 140 18, 220 8 S 318 4, 318 4"
                    fill="none"
                    stroke="var(--accent)"
                    strokeWidth="2.4"
                    strokeLinecap="round"
                  />
                </svg>
              </span>
              .
            </h1>

            <p className="mt-7 max-w-[58ch] text-[1.075rem] leading-[1.75] text-[color:var(--nav-link)] sm:text-lg">
              Wandrix turns the messy stuff &mdash; vague dates, half-ideas,
              budgets you don&rsquo;t want to say out loud &mdash; into a real
              plan. You talk. A live trip board takes shape next to the
              conversation: shortlists, route, days, stays, flights. Nothing
              gets lost in scrollback.
            </p>

            <div className="mt-9 flex flex-wrap items-center gap-3">
              <Link
                href={primaryHref}
                className="group inline-flex min-h-12 items-center gap-2 rounded-full bg-[color:var(--nav-brand-text)] px-6 py-3 text-sm font-semibold text-[color:var(--nav-shell)] transition hover:bg-[color:var(--accent-strong)]"
              >
                Start a trip
                <ArrowRight className="h-4 w-4 transition group-hover:translate-x-0.5" />
              </Link>
              <Link
                href={secondaryHref}
                className="inline-flex min-h-12 items-center gap-2 rounded-full border border-[color:var(--nav-border-strong)] bg-background/60 px-5 py-3 text-sm font-semibold text-[color:var(--nav-brand-text)] transition hover:bg-background/90"
              >
                See how it works
              </Link>
            </div>

            <p className="mt-5 text-xs tracking-wide text-[color:var(--muted-foreground)]">
              Sign in with Google &middot; export trips as a brochure
            </p>

            <div className="mt-12 grid max-w-md grid-cols-3 gap-6 border-t border-[color:var(--nav-border)] pt-6">
              <Stat label="Talk to plan" value="zero forms" />
              <Stat label="Trip board" value="always live" />
              <Stat label="Output" value="a real brochure" />
            </div>
          </div>

          {/* Right: layered chat + suggestion card mock */}
          <div className="relative mx-auto w-full max-w-[680px] lg:max-w-none">
            {/* Floating destination shortlist behind */}
            <div
              className="absolute -right-2 top-2 hidden w-[64%] rotate-[2deg] rounded-2xl border border-[color:var(--nav-border)] bg-background p-4 shadow-[0_28px_70px_-32px_rgba(15,23,42,0.28)] sm:block lg:right-[-2.5rem] lg:top-[-1.5rem] wx-float"
              style={{ animationDelay: "1.2s" }}
            >
              <div className="flex items-center justify-between text-[11px] uppercase tracking-[0.18em] text-[color:var(--muted-foreground)]">
                <span>Shortlist · 4 of 12</span>
                <span className="text-[color:var(--accent-strong)]">
                  &bull; live
                </span>
              </div>
              <div className="mt-3">
                <DestinationCard
                  name="Lisbon coast"
                  region="Portugal"
                  practicality="2h 35m direct from London"
                  fit="Sea views, slow pace, late May"
                  tradeoffs={["Cooler evenings", "Busy on weekends"]}
                  recommended
                  tone="#16695e"
                />
              </div>
              <div className="mt-3 grid grid-cols-3 gap-2">
                <MiniCity name="Cádiz" tone="#a4541f" />
                <MiniCity name="Madeira" tone="#4a5e34" />
                <MiniCity name="Pollença" tone="#7a5a1d" />
              </div>
            </div>

            {/* Chat card */}
            <div className="relative overflow-hidden rounded-2xl border border-[color:var(--nav-border)] bg-background shadow-[0_40px_120px_-50px_rgba(15,23,42,0.35)]">
              <div className="flex items-center justify-between border-b border-[color:var(--nav-border)] bg-[color:var(--nav-shell-strong)] px-5 py-3.5">
                <div className="flex items-center gap-2">
                  <span className="h-2.5 w-2.5 rounded-full bg-[#e0a14a]" />
                  <span className="h-2.5 w-2.5 rounded-full bg-[#cfcabb]" />
                  <span className="h-2.5 w-2.5 rounded-full bg-[#cfcabb]" />
                </div>
                <span className="text-[11px] font-medium tracking-wide text-[color:var(--muted-foreground)]">
                  wandrix &middot; new trip
                </span>
                <span className="text-[11px] text-[color:var(--muted-foreground)]">
                  draft
                </span>
              </div>

              <div className="space-y-4 px-5 py-6 sm:px-6">
                <ChatBubble
                  side="user"
                  text="Three nights somewhere warm in late May. Sea views, easy pace. Not the obvious places."
                />
                <ChatBubble
                  side="assistant"
                  text={
                    <>
                      Got it. I&rsquo;m comparing four shortlists by{" "}
                      <em>practicality, not popularity</em> &mdash; pinning them
                      to the board on the right.
                    </>
                  }
                />
                <div className="flex flex-wrap gap-2 pl-1">
                  <Pin label="Madeira" />
                  <Pin label="Cádiz" />
                  <Pin label="Pollença" />
                  <Pin label="Lisbon coast" leading />
                </div>
                <ChatBubble
                  side="user"
                  text="Lisbon coast feels right. Direct flights only — and keep the pace slow."
                />
                <div className="flex items-center gap-2 pl-1 text-[12px] text-[color:var(--muted-foreground)]">
                  <span className="flex h-6 w-6 items-center justify-center rounded-full bg-[color:var(--accent-soft)]">
                    <Sparkles className="h-3.5 w-3.5 text-[color:var(--accent-strong)]" />
                  </span>
                  Drafting day shape and stay options&hellip;
                  <span className="ml-1 inline-flex gap-1">
                    <Dot delay="0s" />
                    <Dot delay="0.15s" />
                    <Dot delay="0.3s" />
                  </span>
                </div>
              </div>

              <div className="flex items-center gap-2 border-t border-[color:var(--nav-border)] bg-[color:var(--nav-shell-strong)] px-5 py-3">
                <div className="flex-1 truncate rounded-full border border-[color:var(--nav-border)] bg-background px-4 py-2 text-sm text-[color:var(--muted-foreground)]">
                  Add a constraint, swap a city, or ask why&hellip;
                </div>
                <button
                  type="button"
                  className="flex h-9 w-9 items-center justify-center rounded-full bg-[color:var(--nav-brand-text)] text-[color:var(--nav-shell)]"
                  aria-label="Send"
                  disabled
                >
                  <ArrowRight className="h-4 w-4" />
                </button>
              </div>
            </div>

            {/* Floating note */}
            <div className="absolute -left-4 bottom-[-2rem] hidden w-60 -rotate-[3deg] rounded-xl border border-[color:var(--nav-border)] bg-[#fff8e8] p-4 shadow-[0_18px_40px_-20px_rgba(120,90,40,0.4)] sm:block">
              <p className="font-display text-[15px] italic leading-snug text-[#5a4622]">
                &ldquo;The plan kept its shape, even after I changed my
                mind&hellip; twice.&rdquo;
              </p>
              <p className="mt-2 text-[10px] uppercase tracking-[0.18em] text-[#9a7a3a]">
                A scribbled note &middot; an actual trip
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* ============== MARQUEE ============== */}
      <section className="relative overflow-hidden border-b border-[color:var(--nav-border)] bg-[color:var(--nav-shell-strong)] py-6">
        <div className="flex w-max wx-marquee-track">
          {[...marqueePhrases, ...marqueePhrases].map((phrase, i) => (
            <span
              key={`${phrase}-${i}`}
              className="flex shrink-0 items-center gap-6 px-6 font-display text-2xl italic text-[color:var(--nav-brand-text)]/70 sm:text-3xl"
            >
              {phrase}
              <span className="text-[color:var(--accent)]">&middot;</span>
            </span>
          ))}
        </div>
      </section>

      {/* ============== MANIFESTO ============== */}
      <section className="border-b border-[color:var(--nav-border)] bg-background">
        <div className="mx-auto max-w-[1480px] px-4 py-20 sm:px-6 lg:py-28">
          <div className="grid gap-12 lg:grid-cols-[0.32fr_0.68fr] lg:gap-20">
            <div>
              <p className="text-[11px] font-semibold uppercase tracking-[0.22em] text-[color:var(--accent-strong)]">
                The idea
              </p>
              <div className="mt-3 h-px w-12 bg-[color:var(--accent)]" />
            </div>
            <div className="max-w-3xl">
              <p className="font-display text-3xl leading-[1.25] text-[color:var(--nav-brand-text)] sm:text-[2.6rem] sm:leading-[1.2]">
                Most travel tools treat planning as a{" "}
                <span className="italic">form</span>. We treat it as a{" "}
                <span className="italic">conversation</span> &mdash; and the
                conversation deserves a workspace as careful as the trip.
              </p>
              <p className="mt-8 max-w-[60ch] text-base leading-[1.85] text-[color:var(--nav-link)] sm:text-lg">
                Real trips are decided in fragments: a half-formed idea on a
                Tuesday, a rethink on Friday, a nudge from someone you trust.
                Wandrix holds the fragments together &mdash; the chat where you
                think, the board where the plan lives, and the moment they meet
                in the middle.
              </p>

              <div className="mt-12 grid gap-px overflow-hidden rounded-2xl border border-[color:var(--nav-border)] bg-[color:var(--nav-border)] sm:grid-cols-3">
                <Belief
                  num="01"
                  title="No forms. Ever."
                  body="If you can describe the trip to a friend, you can plan it here. Drop-downs are not a feature; they are a tax."
                />
                <Belief
                  num="02"
                  title="The board is the source of truth."
                  body="The chat helps you think. The board holds the plan &mdash; editable, exportable, real."
                />
                <Belief
                  num="03"
                  title="Show the working."
                  body="Every shortlist explains itself: practicality, fit, tradeoffs, and one explicit recommendation. Pin it, swap it, push back."
                />
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ============== HOW IT WORKS / 5 STAGES ============== */}
      <section
        id="how"
        className="border-b border-[color:var(--nav-border)] bg-[color:var(--nav-shell)]"
      >
        <div className="mx-auto max-w-[1480px] px-4 py-20 sm:px-6 lg:py-28">
          <div className="flex flex-col items-start justify-between gap-6 sm:flex-row sm:items-end">
            <div className="max-w-2xl">
              <p className="text-[11px] font-semibold uppercase tracking-[0.22em] text-[color:var(--accent-strong)]">
                How a trip moves
              </p>
              <h2 className="mt-4 font-display text-4xl leading-[1.1] sm:text-5xl">
                One conversation.
                <br />
                Five honest stages.
              </h2>
            </div>
            <p className="max-w-sm text-[15px] leading-7 text-[color:var(--nav-link)]">
              No ten-step wizard, no &lsquo;answer 24 questions to begin&rsquo;.
              The planner moves with you, in the order that makes sense for
              your trip.
            </p>
          </div>

          {/* Staircase of 5 stages, alternating sides */}
          <div className="relative mt-14 space-y-8">
            <Stage
              num="01"
              kicker="The brief"
              title="Tell it what you actually want."
              body="Skip the trip-type checklist. Say it the way you&rsquo;d say it to a friend &mdash; pace, dates, who&rsquo;s coming, the things you&rsquo;d rather not do."
              align="left"
              tint="sage"
              visual={<BriefVisual />}
            />
            <Stage
              num="02"
              kicker="Shortlists, with working shown"
              title="Destinations ranked by practicality, not popularity."
              body="Each card explains its fit, gives one explicit recommendation, and lists the tradeoffs you&rsquo;d trip over. Pin one to lead. Swap whenever."
              align="right"
              tint="ocean"
              visual={<ShortlistVisual />}
            />
            <Stage
              num="03"
              kicker="Direction, pace, tradeoffs"
              title="Decide the shape of the trip before pinning the days."
              body="Slow or full? Culture-led or food-led? One stop or three? The planner reads your answers and biases everything downstream &mdash; stays, activities, even the route."
              align="left"
              tint="ember"
              visual={<TripStyleVisual />}
            />
            <Stage
              num="04"
              kicker="Stays, flights, days"
              title="A live board that holds the whole plan, in one frame."
              body="Days shaped morning / afternoon / evening. Hotels filterable by area, style and nightly rate. Flights presented as honest tradeoffs. Weather quietly nudging the plan."
              align="right"
              tint="sand"
              visual={<BoardVisual />}
            />
            <Stage
              num="05"
              kicker="The brochure"
              title="A real document. Not a chat transcript."
              body="When the plan&rsquo;s right, one click turns it into a multi-page brochure: route map, day-by-day plan, stays, the things you said you cared about. Yours to keep, share, or hand to whoever&rsquo;s booking."
              align="left"
              tint="ink"
              visual={<BrochureVisual />}
            />
          </div>
        </div>
      </section>

      {/* ============== ANATOMY OF THE BOARD ============== */}
      <section className="border-b border-[color:var(--nav-border)] bg-background">
        <div className="mx-auto max-w-[1480px] px-4 py-20 sm:px-6 lg:py-24">
          <div className="grid gap-12 lg:grid-cols-[0.4fr_0.6fr] lg:items-end">
            <div className="max-w-xl">
              <p className="text-[11px] font-semibold uppercase tracking-[0.22em] text-[color:var(--accent-strong)]">
                Anatomy of the board
              </p>
              <h2 className="mt-4 font-display text-4xl leading-[1.1] sm:text-5xl">
                Eight things the board
                <br />
                quietly takes care of.
              </h2>
              <p className="mt-6 max-w-md text-[15px] leading-[1.85] text-[color:var(--nav-link)]">
                The chat is the friendly bit. The board is the engineering.
                Every piece exists to keep the plan honest while you keep
                talking.
              </p>
            </div>
          </div>

          <div className="mt-12 grid gap-px overflow-hidden rounded-2xl border border-[color:var(--nav-border)] bg-[color:var(--nav-border)] sm:grid-cols-2 lg:grid-cols-4">
            <BoardFeature
              icon={<MapPinned className="h-[1.125rem] w-[1.125rem]" />}
              title="Route logic"
              body="Cities ordered by what flows, not just what fits."
            />
            <BoardFeature
              icon={<Clock className="h-[1.125rem] w-[1.125rem]" />}
              title="Day shape"
              body="Mornings, afternoons, evenings &mdash; planned, not stuffed."
            />
            <BoardFeature
              icon={<CloudSun className="h-[1.125rem] w-[1.125rem]" />}
              title="Weather-aware"
              body="Forecasts nudge the day, never override it."
            />
            <BoardFeature
              icon={<Hotel className="h-[1.125rem] w-[1.125rem]" />}
              title="Hotel filters"
              body="Area, style, nightly rate, sort by fit. No rank-buying."
            />
            <BoardFeature
              icon={<Plane className="h-[1.125rem] w-[1.125rem]" />}
              title="Flight tradeoffs"
              body="Direct, one-stop saver, keep flexible &mdash; honestly framed."
            />
            <BoardFeature
              icon={<Layers className="h-[1.125rem] w-[1.125rem]" />}
              title="Activity shortlists"
              body="Essential, maybe, passed. Drop in or out without guilt."
            />
            <BoardFeature
              icon={<GitBranch className="h-[1.125rem] w-[1.125rem]" />}
              title="Conflict tracking"
              body="When a change knocks something else, the board says so."
            />
            <BoardFeature
              icon={<BookOpenText className="h-[1.125rem] w-[1.125rem]" />}
              title="Brochure export"
              body="One click. A polished, shareable document."
            />
          </div>
        </div>
      </section>

      {/* ============== SCENARIOS ============== */}
      <section className="border-b border-[color:var(--nav-border)] bg-[color:var(--nav-shell)]">
        <div className="mx-auto max-w-[1480px] px-4 py-20 sm:px-6 lg:py-28">
          <div className="flex flex-col items-start justify-between gap-6 sm:flex-row sm:items-end">
            <div className="max-w-2xl">
              <p className="text-[11px] font-semibold uppercase tracking-[0.22em] text-[color:var(--accent-strong)]">
                Briefs, not bullet points
              </p>
              <h2 className="mt-4 font-display text-4xl leading-[1.1] sm:text-5xl">
                Six trips, in the words a real
                <br />
                traveller would actually use.
              </h2>
            </div>
            <Link
              href={primaryHref}
              className="inline-flex items-center gap-1.5 text-sm font-semibold text-[color:var(--nav-brand-text)] underline-offset-4 hover:underline"
            >
              Start one of these
              <ArrowUpRight className="h-4 w-4" />
            </Link>
          </div>

          <div className="mt-12 grid gap-5 md:grid-cols-2 lg:grid-cols-3">
            {scenarios.map((s, i) => {
              const t = toneStyles[s.tone];
              return (
                <article
                  key={s.title}
                  className="group relative flex flex-col justify-between overflow-hidden rounded-2xl border border-[color:var(--nav-border)] p-6 transition hover:-translate-y-0.5 hover:shadow-[0_24px_60px_-30px_rgba(15,23,42,0.25)]"
                  style={{ background: t.bg, animationDelay: `${i * 60}ms` }}
                >
                  <div>
                    <span
                      className="inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-[11px] font-semibold uppercase tracking-[0.14em]"
                      style={{ background: t.chip, color: t.accent }}
                    >
                      <Compass className="h-3 w-3" />
                      {s.tag}
                    </span>
                    <h3
                      className="mt-5 font-display text-3xl leading-tight"
                      style={{ color: t.accent }}
                    >
                      {s.title}
                    </h3>
                    <p
                      className="mt-4 text-[15px] leading-7"
                      style={{ color: "rgba(20,30,28,0.78)" }}
                    >
                      &ldquo;{s.brief}&rdquo;
                    </p>
                  </div>
                  <div
                    className="mt-7 flex items-center justify-between border-t pt-4 text-[12px]"
                    style={{
                      borderColor: "rgba(20,30,28,0.12)",
                      color: t.accent,
                    }}
                  >
                    <span className="font-semibold tracking-wide">
                      {s.meta}
                    </span>
                    <ArrowUpRight className="h-4 w-4 opacity-60 transition group-hover:translate-x-0.5 group-hover:-translate-y-0.5 group-hover:opacity-100" />
                  </div>
                </article>
              );
            })}
          </div>
        </div>
      </section>

      {/* ============== SPECIALIST WORKSPACES ============== */}
      <section className="border-b border-[color:var(--nav-border)] bg-background">
        <div className="mx-auto max-w-[1480px] px-4 py-20 sm:px-6 lg:py-24">
          <div className="grid gap-12 lg:grid-cols-[0.4fr_0.6fr] lg:items-center">
            <div className="max-w-xl">
              <p className="text-[11px] font-semibold uppercase tracking-[0.22em] text-[color:var(--accent-strong)]">
                When you want a closer look
              </p>
              <h2 className="mt-4 font-display text-4xl leading-[1.1] sm:text-5xl">
                Four lenses on the same trip.
              </h2>
              <p className="mt-6 max-w-md text-[15px] leading-[1.85] text-[color:var(--nav-link)]">
                Flights, hotels, activities and weather each get a focused
                workspace when you ask for one. They open inside your trip,
                share its context, and hand you back to the chat when
                you&rsquo;re done.
              </p>
              <div className="mt-8 flex flex-wrap gap-3">
                <Tag>One trip context</Tag>
                <Tag>Shared with the board</Tag>
                <Tag>Easy to abandon</Tag>
              </div>
            </div>

            <div className="grid gap-4 sm:grid-cols-2">
              <SpecCard
                icon={<Plane className="h-5 w-5" />}
                title="Flights"
                tone="#16695e"
                lines={[
                  "Direct, one-stop saver, keep flexible",
                  "Returns that respect your last day",
                  "Honest red-eye warnings",
                ]}
              />
              <SpecCard
                icon={<Hotel className="h-5 w-5" />}
                title="Hotels"
                tone="#a4541f"
                lines={[
                  "Filter by area, style, nightly rate",
                  "Sort by fit, not by who paid",
                  "Shortlist a few, swap one in",
                ]}
              />
              <SpecCard
                icon={<MapPinned className="h-5 w-5" />}
                title="Activities"
                tone="#4a5e34"
                lines={[
                  "Essential / maybe / passed buckets",
                  "Built around your day shape",
                  "Drop one without guilt",
                ]}
              />
              <SpecCard
                icon={<CloudSun className="h-5 w-5" />}
                title="Weather"
                tone="#7a5a1d"
                lines={[
                  "Forecast across every day",
                  "Nudges day order, not your plan",
                  "Flags trips that need rethinking",
                ]}
              />
            </div>
          </div>
        </div>
      </section>

      {/* ============== FAQ ============== */}
      <section className="border-b border-[color:var(--nav-border)] bg-[color:var(--nav-shell)]">
        <div className="mx-auto max-w-[1480px] px-4 py-20 sm:px-6 lg:py-24">
          <div className="grid gap-12 lg:grid-cols-[0.36fr_0.64fr] lg:gap-20">
            <div>
              <p className="text-[11px] font-semibold uppercase tracking-[0.22em] text-[color:var(--accent-strong)]">
                Honest answers
              </p>
              <h2 className="mt-4 font-display text-4xl leading-[1.1] sm:text-5xl">
                The five questions
                <br />
                everyone asks.
              </h2>
              <p className="mt-6 max-w-sm text-[15px] leading-[1.85] text-[color:var(--nav-link)]">
                We&rsquo;d rather under-promise the product and over-deliver
                the trip.
              </p>
            </div>

            <div className="divide-y divide-[color:var(--nav-border)] border-y border-[color:var(--nav-border)]">
              {faqs.map((f) => (
                <details
                  key={f.q}
                  className="group py-5 [&_summary::-webkit-details-marker]:hidden"
                >
                  <summary className="flex cursor-pointer items-start justify-between gap-6 text-left">
                    <span className="font-display text-xl text-[color:var(--nav-brand-text)] sm:text-2xl">
                      {f.q}
                    </span>
                    <span className="mt-1 flex h-7 w-7 shrink-0 items-center justify-center rounded-full border border-[color:var(--nav-border-strong)] text-[color:var(--nav-brand-text)] transition group-open:rotate-45 group-open:bg-[color:var(--nav-brand-text)] group-open:text-[color:var(--nav-shell)]">
                      <span className="text-xl leading-none">+</span>
                    </span>
                  </summary>
                  <p
                    className="mt-4 max-w-3xl text-[15px] leading-[1.85] text-[color:var(--nav-link)]"
                    dangerouslySetInnerHTML={{ __html: f.a }}
                  />
                </details>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* ============== FINAL CTA ============== */}
      <section className="relative overflow-hidden bg-[color:var(--nav-brand-text)] text-[color:var(--nav-shell)]">
        <div
          aria-hidden
          className="pointer-events-none absolute inset-0 opacity-30"
          style={{
            background:
              "radial-gradient(circle at 18% 20%, rgba(132,204,22,0.22) 0%, transparent 45%), radial-gradient(circle at 82% 80%, rgba(196,140,80,0.28) 0%, transparent 45%)",
          }}
        />
        <div className="relative mx-auto max-w-[1480px] px-4 py-20 sm:px-6 lg:py-28">
          <div className="grid gap-10 lg:grid-cols-[0.62fr_0.38fr] lg:items-end">
            <div>
              <p className="text-[11px] font-semibold uppercase tracking-[0.22em] text-[color:var(--brand-sun)]">
                Open the planner
              </p>
              <h2 className="mt-5 max-w-[18ch] font-display text-5xl leading-[1.05] sm:text-6xl lg:text-7xl">
                Your next trip is one
                <br />
                <span className="italic text-[color:var(--brand-sun)]">
                  sentence
                </span>{" "}
                away.
              </h2>
              <p className="mt-6 max-w-[52ch] text-[15px] leading-[1.85] text-[color:var(--nav-shell)]/80 sm:text-base">
                Type a brief, watch the board take shape, and walk away with a
                brochure-ready itinerary. Wandrix isn&rsquo;t trying to replace
                travel agents &mdash; it&rsquo;s trying to be the planning
                workspace you actually wanted all along.
              </p>
            </div>
            <div className="flex flex-col gap-3 lg:items-end">
              <Link
                href={primaryHref}
                className="group inline-flex min-h-12 items-center justify-center gap-2 rounded-full bg-[color:var(--brand-sun)] px-7 py-3.5 text-sm font-semibold text-[color:var(--nav-brand-text)] transition hover:bg-white"
              >
                Start a trip
                <ArrowRight className="h-4 w-4 transition group-hover:translate-x-0.5" />
              </Link>
              <Link
                href="#how"
                className="inline-flex min-h-12 items-center justify-center gap-2 rounded-full border border-white/20 px-6 py-3 text-sm font-semibold text-[color:var(--nav-shell)] transition hover:bg-white/10"
              >
                Re-read how it works
              </Link>
              <p className="mt-1 inline-flex items-center gap-1.5 text-[11px] tracking-wide text-[color:var(--nav-shell)]/60">
                <ShieldCheck className="h-3.5 w-3.5" />
                Sign in with Google · trips saved automatically
              </p>
            </div>
          </div>
        </div>
      </section>
    </main>
  );
}

/* ====================================================================
 * Small inline components
 * ==================================================================== */

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <p className="font-display text-xl text-[color:var(--nav-brand-text)] sm:text-2xl">
        {value}
      </p>
      <p className="mt-1 text-[11px] uppercase tracking-[0.18em] text-[color:var(--muted-foreground)]">
        {label}
      </p>
    </div>
  );
}

function ChatBubble({
  side,
  text,
}: {
  side: "user" | "assistant";
  text: React.ReactNode;
}) {
  if (side === "user") {
    return (
      <div className="flex justify-end">
        <div className="max-w-[78%] rounded-2xl rounded-tr-md bg-[color:var(--nav-brand-text)] px-4 py-2.5 text-[14px] leading-6 text-[color:var(--nav-shell)] shadow-sm">
          {text}
        </div>
      </div>
    );
  }
  return (
    <div className="flex items-start gap-3">
      <div className="mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-[color:var(--accent-soft)] text-[color:var(--accent-strong)]">
        <Sparkles className="h-3.5 w-3.5" />
      </div>
      <div className="max-w-[82%] rounded-2xl rounded-tl-md border border-[color:var(--nav-border)] bg-[color:var(--nav-shell-strong)] px-4 py-2.5 text-[14px] leading-6 text-[color:var(--nav-brand-text)]">
        {text}
      </div>
    </div>
  );
}

function Pin({ label, leading }: { label: string; leading?: boolean }) {
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full border px-3 py-1 text-[12px] font-medium shadow-sm ${
        leading
          ? "border-[color:var(--accent)] bg-[color:var(--accent-soft)] text-[color:var(--accent-strong)]"
          : "border-[color:var(--nav-border)] bg-background text-[color:var(--nav-brand-text)]"
      }`}
    >
      <span
        className={`h-1.5 w-1.5 rounded-full ${
          leading ? "bg-[color:var(--accent)]" : "bg-[color:var(--accent)]"
        }`}
      />
      {label}
      {leading ? (
        <span className="ml-1 rounded-full bg-[color:var(--accent)] px-1.5 py-px text-[9px] font-semibold uppercase tracking-wider text-white">
          Leading
        </span>
      ) : null}
    </span>
  );
}

function Dot({ delay }: { delay: string }) {
  return (
    <span
      className="inline-block h-1.5 w-1.5 animate-bounce rounded-full bg-[color:var(--accent)]"
      style={{ animationDelay: delay }}
    />
  );
}

function DestinationCard({
  name,
  region,
  practicality,
  fit,
  tradeoffs,
  recommended,
  tone,
}: {
  name: string;
  region: string;
  practicality: string;
  fit: string;
  tradeoffs: string[];
  recommended?: boolean;
  tone: string;
}) {
  return (
    <div className="overflow-hidden rounded-xl border border-[color:var(--nav-border)] bg-[color:var(--nav-shell-strong)]">
      <div
        className="relative h-20"
        style={{
          background: `linear-gradient(135deg, ${tone}, ${tone}cc 55%, ${tone}88)`,
        }}
      >
        <div className="absolute inset-0 wx-grain opacity-30" />
        {recommended ? (
          <span className="absolute right-2 top-2 rounded-full bg-white/90 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider text-[color:var(--accent-strong)]">
            Recommended
          </span>
        ) : null}
        <div className="absolute bottom-2 left-3 text-white">
          <p className="text-[10px] uppercase tracking-[0.18em] opacity-80">
            {region}
          </p>
          <p className="font-display text-lg leading-tight">{name}</p>
        </div>
      </div>
      <div className="space-y-2 px-3 py-2.5">
        <div className="flex items-center gap-1.5 text-[11px] text-[color:var(--nav-link)]">
          <Plane className="h-3 w-3 text-[color:var(--accent-strong)]" />
          {practicality}
        </div>
        <div className="flex items-center gap-1.5 text-[11px] text-[color:var(--nav-link)]">
          <Sun className="h-3 w-3 text-[color:var(--accent-strong)]" />
          {fit}
        </div>
        <div className="flex flex-wrap gap-1 pt-1">
          {tradeoffs.map((t) => (
            <span
              key={t}
              className="rounded-md border border-[color:var(--nav-border)] bg-background px-1.5 py-0.5 text-[10px] text-[color:var(--muted-foreground)]"
            >
              {t}
            </span>
          ))}
        </div>
      </div>
    </div>
  );
}

function MiniCity({ name, tone }: { name: string; tone: string }) {
  return (
    <div className="rounded-lg border border-[color:var(--nav-border)] bg-[color:var(--nav-shell-strong)] p-1.5">
      <div
        className="h-8 rounded"
        style={{ background: `linear-gradient(135deg, ${tone}, ${tone}99)` }}
      />
      <p className="mt-1 text-[11px] font-semibold text-[color:var(--nav-brand-text)]">
        {name}
      </p>
    </div>
  );
}

function Belief({
  num,
  title,
  body,
}: {
  num: string;
  title: string;
  body: string;
}) {
  return (
    <div className="bg-background p-7">
      <p className="font-display text-3xl italic text-[color:var(--accent-strong)]">
        {num}
      </p>
      <h3 className="mt-3 font-display text-2xl text-[color:var(--nav-brand-text)]">
        {title}
      </h3>
      <p className="mt-3 text-[14px] leading-7 text-[color:var(--nav-link)]">
        {body}
      </p>
    </div>
  );
}

type StageTint = "sage" | "ocean" | "ember" | "sand" | "ink";

const stageTintBg: Record<StageTint, string> = {
  sage:
    "linear-gradient(145deg, #f3f5ec 0%, #e8ecdb 100%)",
  ocean:
    "linear-gradient(145deg, #eef5f3 0%, #dceae5 100%)",
  ember:
    "linear-gradient(145deg, #fbeee2 0%, #f3d6bc 100%)",
  sand:
    "linear-gradient(145deg, #faf3e2 0%, #f0e2bd 100%)",
  ink:
    "linear-gradient(145deg, #ecefee 0%, #d9dee0 100%)",
};

function Stage({
  num,
  kicker,
  title,
  body,
  align,
  tint,
  visual,
}: {
  num: string;
  kicker: string;
  title: string;
  body: string;
  align: "left" | "right";
  tint: StageTint;
  visual: React.ReactNode;
}) {
  return (
    <article className="relative grid gap-10 overflow-hidden rounded-3xl border border-[color:var(--nav-border)] bg-background p-6 sm:p-10 lg:grid-cols-[0.48fr_0.52fr] lg:items-stretch lg:gap-14 lg:p-12">
      {/* Watermark numeral */}
      <span
        aria-hidden
        className="pointer-events-none absolute -right-4 -top-8 select-none font-display text-[14rem] font-bold leading-none text-[color:var(--nav-brand-text)]/[0.035] lg:text-[22rem]"
      >
        {num}
      </span>

      <div
        className={`relative flex min-h-[360px] items-center justify-center rounded-2xl p-6 sm:p-8 ${
          align === "right" ? "lg:order-2" : ""
        }`}
        style={{ background: stageTintBg[tint] }}
      >
        <div className="absolute inset-0 wx-grain rounded-2xl opacity-40" />
        <div className="relative w-full">{visual}</div>
      </div>

      <div className="relative flex flex-col justify-center">
        <div className="flex items-center gap-3">
          <span className="font-display text-3xl italic text-[color:var(--accent-strong)]">
            {num}
          </span>
          <span className="h-px flex-1 max-w-[3rem] bg-[color:var(--nav-border-strong)]" />
          <span className="rounded-full border border-[color:var(--nav-border)] px-2.5 py-1 text-[10px] font-semibold uppercase tracking-[0.18em] text-[color:var(--nav-link)]">
            {kicker}
          </span>
        </div>
        <h3 className="mt-5 font-display text-3xl leading-[1.15] text-[color:var(--nav-brand-text)] sm:text-[2.3rem]">
          {title}
        </h3>
        <p
          className="mt-5 max-w-[52ch] text-[15px] leading-[1.85] text-[color:var(--nav-link)] sm:text-base"
          dangerouslySetInnerHTML={{ __html: body }}
        />
      </div>
    </article>
  );
}

/* ----- Stage visuals (custom, product-authentic, no AI-stock vibe) ----- */

function BriefVisual() {
  return (
    <div className="space-y-6">
      <div className="relative rounded-2xl border border-[color:var(--nav-border)] bg-white/90 p-6 shadow-[0_18px_50px_-30px_rgba(15,23,42,0.2)] sm:p-7">
        <div className="flex items-center justify-between">
          <span className="text-[11px] font-semibold uppercase tracking-[0.18em] text-[color:var(--muted-foreground)]">
            Tuesday, 21:14
          </span>
          <span className="flex items-center gap-1.5 text-[11px] text-[color:var(--muted-foreground)]">
            <span className="h-1.5 w-1.5 rounded-full bg-[color:var(--accent)]" />
            You
          </span>
        </div>
        <p className="mt-4 font-display text-[1.5rem] leading-[1.3] text-[color:var(--nav-brand-text)] sm:text-[1.8rem]">
          &ldquo;A four-night break in late May. Sea views, slow mornings.{" "}
          <span className="italic text-[color:var(--accent-strong)]">
            Nothing that needs a 6am flight.
          </span>
          &rdquo;
        </p>
      </div>

      <div className="relative">
        <div className="absolute left-6 -top-3 text-[color:var(--muted-foreground)]">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none">
            <path
              d="M12 4v16m0 0l-6-6m6 6l6-6"
              stroke="currentColor"
              strokeWidth="1.5"
              strokeLinecap="round"
            />
          </svg>
        </div>
        <div className="rounded-xl border border-dashed border-[color:var(--nav-border-strong)] bg-white/60 p-4">
          <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-[color:var(--muted-foreground)]">
            What the planner extracted
          </p>
          <div className="mt-3 flex flex-wrap gap-2">
            <Token>4 nights</Token>
            <Token>late May</Token>
            <Token>sea views</Token>
            <Token>slow pace</Token>
            <Token tone="warn">no early flights</Token>
          </div>
        </div>
      </div>
    </div>
  );
}

function Token({
  children,
  tone,
}: {
  children: React.ReactNode;
  tone?: "warn";
}) {
  if (tone === "warn") {
    return (
      <span className="inline-flex items-center rounded-full border border-[#c97d3a]/30 bg-[#fbeee2] px-3 py-1 text-[12px] font-medium text-[#7a3e0e]">
        {children}
      </span>
    );
  }
  return (
    <span className="inline-flex items-center rounded-full border border-[color:var(--nav-border)] bg-background px-3 py-1 text-[12px] font-medium text-[color:var(--nav-brand-text)]">
      {children}
    </span>
  );
}

function ShortlistVisual() {
  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-[color:var(--muted-foreground)]">
          Shortlist &middot; 4 of 12
        </p>
        <span className="inline-flex items-center gap-1.5 rounded-full border border-[color:var(--accent)]/30 bg-white/70 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider text-[color:var(--accent-strong)]">
          <span className="h-1.5 w-1.5 rounded-full bg-[color:var(--accent)]" />
          Recommended
        </span>
      </div>
      <DestinationCard
        name="Lisbon coast"
        region="Portugal"
        practicality="2h 35m direct from LHR"
        fit="Sea views, slow pace, late May"
        tradeoffs={["Cooler evenings", "Busy weekends"]}
        recommended
        tone="#16695e"
      />
      <div className="rounded-xl border border-dashed border-[color:var(--nav-border-strong)] bg-white/60 p-3">
        <p className="text-[11px] leading-5 text-[color:var(--nav-link)]">
          <span className="font-semibold text-[color:var(--accent-strong)]">
            Why this leads &middot;
          </span>{" "}
          Matches the &ldquo;no early flights&rdquo; constraint, shortest direct
          route, reliably sunny in late May.
        </p>
      </div>
      <div className="grid grid-cols-3 gap-2">
        <MiniCity name="Cádiz" tone="#a4541f" />
        <MiniCity name="Madeira" tone="#4a5e34" />
        <MiniCity name="Pollença" tone="#7a5a1d" />
      </div>
    </div>
  );
}

function TripStyleVisual() {
  return (
    <div className="space-y-5">
      <div className="rounded-2xl border border-[color:var(--nav-border)] bg-white/90 p-5 shadow-[0_18px_50px_-30px_rgba(15,23,42,0.15)]">
        <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-[color:var(--muted-foreground)]">
          Direction
        </p>
        <div className="mt-3 grid grid-cols-2 gap-2">
          <Choice icon={<Utensils className="h-3.5 w-3.5" />} active>
            Food-led
          </Choice>
          <Choice icon={<Waves className="h-3.5 w-3.5" />}>Coastal</Choice>
          <Choice>Culture</Choice>
          <Choice>Outdoors</Choice>
        </div>
      </div>

      <div className="rounded-2xl border border-[color:var(--nav-border)] bg-white/90 p-5 shadow-[0_18px_50px_-30px_rgba(15,23,42,0.15)]">
        <div className="flex items-center justify-between">
          <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-[color:var(--muted-foreground)]">
            Pace
          </p>
          <span className="font-display text-base italic text-[color:var(--accent-strong)]">
            Slow
          </span>
        </div>
        <div className="relative mt-4 h-2.5 rounded-full bg-[color:var(--nav-border)]">
          <div
            className="absolute inset-y-0 left-0 rounded-full bg-gradient-to-r from-[color:var(--accent-strong)] to-[color:var(--accent)]"
            style={{ width: "28%" }}
          />
          <div
            className="absolute -top-1.5 h-5 w-5 rounded-full border-[3px] border-white bg-[color:var(--accent-strong)] shadow"
            style={{ left: "calc(28% - 10px)" }}
          />
        </div>
        <div className="mt-3 flex justify-between text-[11px] text-[color:var(--muted-foreground)]">
          <span>Slow</span>
          <span>Balanced</span>
          <span>Full</span>
        </div>
      </div>

      <div className="rounded-2xl border border-[color:var(--nav-border)] bg-white/90 p-5 shadow-[0_18px_50px_-30px_rgba(15,23,42,0.15)]">
        <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-[color:var(--muted-foreground)]">
          Tradeoffs
        </p>
        <div className="mt-3 space-y-4">
          <Tradeoff label="Splurge stay" left="None" right="One night" pos={68} />
          <Tradeoff
            label="Routing"
            left="Single base"
            right="Hop around"
            pos={22}
          />
        </div>
      </div>
    </div>
  );
}

function Choice({
  children,
  icon,
  active,
}: {
  children: React.ReactNode;
  icon?: React.ReactNode;
  active?: boolean;
}) {
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full border px-3 py-1.5 text-[12px] font-medium ${
        active
          ? "border-[color:var(--accent)] bg-[color:var(--accent-soft)] text-[color:var(--accent-strong)]"
          : "border-[color:var(--nav-border)] bg-background text-[color:var(--nav-brand-text)]"
      }`}
    >
      {icon}
      {children}
    </span>
  );
}

function Tradeoff({
  label,
  left,
  right,
  pos,
}: {
  label: string;
  left: string;
  right: string;
  pos: number;
}) {
  return (
    <div>
      <div className="flex items-center justify-between text-[11px] text-[color:var(--nav-link)]">
        <span className="font-medium">{label}</span>
        <span className="text-[color:var(--muted-foreground)]">
          {left} &middot; {right}
        </span>
      </div>
      <div className="relative mt-1 h-1.5 rounded-full bg-[color:var(--nav-border)]">
        <div
          className="absolute -top-1 h-3.5 w-3.5 rounded-full border-2 border-white bg-[color:var(--accent)] shadow"
          style={{ left: `calc(${pos}% - 7px)` }}
        />
      </div>
    </div>
  );
}

function BoardVisual() {
  const days = [
    { day: "Thu", date: "22", w: "☀", temp: "24°", title: "Arrive Lisbon", part: "Easy" },
    { day: "Fri", date: "23", w: "☀", temp: "25°", title: "Sintra", part: "Day trip" },
    { day: "Sat", date: "24", w: "⛅", temp: "22°", title: "Cascais", part: "Beach" },
    { day: "Sun", date: "25", w: "☀", temp: "26°", title: "Alfama", part: "Food" },
  ];
  return (
    <div className="space-y-4">
      {/* Trip header */}
      <div className="flex items-center justify-between rounded-2xl border border-[color:var(--nav-border)] bg-white/95 p-4 shadow-[0_18px_50px_-30px_rgba(15,23,42,0.18)]">
        <div>
          <p className="font-display text-[1.3rem] leading-tight text-[color:var(--nav-brand-text)]">
            Lisbon coast &middot; 4 nights
          </p>
          <p className="mt-0.5 text-[11px] text-[color:var(--muted-foreground)]">
            May 22 &ndash; 26 &middot; 2 travellers &middot; direct only
          </p>
        </div>
        <div className="text-right">
          <p className="font-display text-2xl text-[color:var(--accent-strong)]">
            £1,840
          </p>
          <p className="text-[10px] uppercase tracking-wider text-[color:var(--muted-foreground)]">
            per person
          </p>
        </div>
      </div>

      {/* Day strip */}
      <div className="rounded-2xl border border-[color:var(--nav-border)] bg-white/95 p-3 shadow-[0_18px_50px_-30px_rgba(15,23,42,0.15)]">
        <div className="flex items-center justify-between px-1 pb-2">
          <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-[color:var(--muted-foreground)]">
            Days
          </p>
          <p className="flex items-center gap-1 text-[10px] text-[color:var(--muted-foreground)]">
            <CloudSun className="h-3 w-3 text-[color:var(--accent-strong)]" />
            Weather-aware
          </p>
        </div>
        <div className="grid grid-cols-4 gap-2">
          {days.map((d) => (
            <div
              key={d.date}
              className="rounded-xl border border-[color:var(--nav-border)] bg-[color:var(--nav-shell-strong)] p-2.5"
            >
              <div className="flex items-center justify-between">
                <span className="text-[10px] font-semibold uppercase tracking-wide text-[color:var(--muted-foreground)]">
                  {d.day} {d.date}
                </span>
                <span className="text-[10px] text-[color:var(--nav-link)]">
                  {d.w} {d.temp}
                </span>
              </div>
              <div className="mt-2 flex items-center gap-0.5">
                <span className="h-1 flex-1 rounded-full bg-[color:var(--accent)]/40" />
                <span className="h-1 flex-1 rounded-full bg-[color:var(--accent)]" />
                <span className="h-1 flex-1 rounded-full bg-[#e0a14a]" />
              </div>
              <p className="mt-2 text-[11px] font-semibold leading-tight text-[color:var(--nav-brand-text)]">
                {d.title}
              </p>
              <p className="text-[10px] text-[color:var(--muted-foreground)]">
                {d.part}
              </p>
            </div>
          ))}
        </div>
      </div>

      {/* Hotel filters */}
      <div className="rounded-2xl border border-[color:var(--nav-border)] bg-white/95 p-3 shadow-[0_18px_50px_-30px_rgba(15,23,42,0.15)]">
        <div className="flex flex-wrap items-center gap-2">
          <Hotel className="h-3.5 w-3.5 text-[color:var(--accent-strong)]" />
          <span className="text-[11px] font-semibold text-[color:var(--nav-brand-text)]">
            Hotels
          </span>
          <FilterChip>Old Town</FilterChip>
          <FilterChip>Boutique</FilterChip>
          <FilterChip>≤ £180/nt</FilterChip>
          <span className="ml-auto text-[10px] text-[color:var(--muted-foreground)]">
            Sort: best fit
          </span>
        </div>
      </div>

      {/* Flight tradeoffs */}
      <div className="grid grid-cols-3 gap-2">
        <FlightOption title="Direct" sub="2h 35m" active />
        <FlightOption title="One-stop" sub="−£120" />
        <FlightOption title="Flexible" sub="Decide later" />
      </div>
    </div>
  );
}

function FilterChip({ children }: { children: React.ReactNode }) {
  return (
    <span className="rounded-full border border-[color:var(--nav-border)] bg-[color:var(--nav-shell-strong)] px-2 py-0.5 text-[10px] font-medium text-[color:var(--nav-link)]">
      {children}
    </span>
  );
}

function FlightOption({
  title,
  sub,
  active,
}: {
  title: string;
  sub: string;
  active?: boolean;
}) {
  return (
    <div
      className={`rounded-lg border p-2 text-center text-[11px] ${
        active
          ? "border-[color:var(--accent)] bg-[color:var(--accent-soft)] text-[color:var(--accent-strong)]"
          : "border-[color:var(--nav-border)] bg-background text-[color:var(--nav-link)]"
      }`}
    >
      <p className="font-semibold">{title}</p>
      <p className="text-[10px] opacity-80">{sub}</p>
    </div>
  );
}

function BrochureVisual() {
  return (
    <div className="relative">
      {/* Rear pages */}
      <div
        aria-hidden
        className="absolute inset-x-6 top-2 h-6 rotate-[-2deg] rounded-t-xl border border-[color:var(--nav-border)] bg-white shadow-[0_10px_30px_-20px_rgba(15,23,42,0.3)]"
      />
      <div
        aria-hidden
        className="absolute inset-x-3 top-5 h-6 rotate-[1.2deg] rounded-t-xl border border-[color:var(--nav-border)] bg-white shadow-[0_10px_30px_-20px_rgba(15,23,42,0.3)]"
      />

      {/* Main brochure page */}
      <div className="relative overflow-hidden rounded-2xl border border-[color:var(--nav-border)] bg-white shadow-[0_30px_80px_-30px_rgba(15,23,42,0.35)]">
        {/* Cover band */}
        <div className="relative h-28 bg-gradient-to-br from-[#16695e] via-[#2d8a7c] to-[#84cc16] p-4">
          <div className="absolute inset-0 wx-grain opacity-30" />
          <div className="relative flex items-start justify-between text-white">
            <div>
              <p className="text-[9px] font-semibold uppercase tracking-[0.22em] opacity-80">
                Wandrix &middot; Trip brochure
              </p>
              <p className="mt-1 font-display text-[1.3rem] leading-tight">
                Lisbon coast, late May
              </p>
              <p className="mt-0.5 text-[11px] opacity-80">
                4 nights &middot; 2 travellers
              </p>
            </div>
            <BookOpenText className="h-5 w-5 opacity-80" />
          </div>
        </div>

        {/* Page body */}
        <div className="grid grid-cols-5 gap-3 p-4">
          <div className="col-span-2 space-y-1.5">
            <p className="text-[9px] font-semibold uppercase tracking-[0.18em] text-[color:var(--muted-foreground)]">
              Route
            </p>
            <div className="flex items-center gap-1.5">
              <span className="h-1.5 w-1.5 rounded-full bg-[#16695e]" />
              <span className="text-[11px] font-medium text-[color:var(--nav-brand-text)]">
                Lisbon
              </span>
            </div>
            <div className="ml-[3px] h-3 w-px bg-[color:var(--nav-border-strong)]" />
            <div className="flex items-center gap-1.5">
              <span className="h-1.5 w-1.5 rounded-full bg-[#a4541f]" />
              <span className="text-[11px] font-medium text-[color:var(--nav-brand-text)]">
                Sintra
              </span>
            </div>
            <div className="ml-[3px] h-3 w-px bg-[color:var(--nav-border-strong)]" />
            <div className="flex items-center gap-1.5">
              <span className="h-1.5 w-1.5 rounded-full bg-[#4a5e34]" />
              <span className="text-[11px] font-medium text-[color:var(--nav-brand-text)]">
                Cascais
              </span>
            </div>
          </div>
          <div className="col-span-3 space-y-2">
            <p className="text-[9px] font-semibold uppercase tracking-[0.18em] text-[color:var(--muted-foreground)]">
              Day 1 &middot; Thu 22
            </p>
            <div className="space-y-1">
              <div className="h-1.5 rounded-full bg-[color:var(--nav-border)]" />
              <div className="h-1.5 w-[88%] rounded-full bg-[color:var(--nav-border)]" />
              <div className="h-1.5 w-[72%] rounded-full bg-[color:var(--nav-border)]" />
            </div>
            <div className="flex gap-2 pt-1">
              <div className="h-10 flex-1 rounded-md bg-[color:var(--nav-shell-strong)]" />
              <div className="h-10 flex-1 rounded-md bg-[color:var(--nav-shell-strong)]" />
            </div>
          </div>
        </div>

        {/* Footer strip */}
        <div className="flex items-center justify-between border-t border-[color:var(--nav-border)] bg-[color:var(--nav-shell)] px-4 py-2">
          <p className="text-[9px] uppercase tracking-[0.18em] text-[color:var(--muted-foreground)]">
            Page 1 of 6
          </p>
          <p className="text-[9px] uppercase tracking-[0.18em] text-[color:var(--accent-strong)]">
            Export as PDF &middot; one click
          </p>
        </div>
      </div>
    </div>
  );
}

function BoardFeature({
  icon,
  title,
  body,
}: {
  icon: React.ReactNode;
  title: string;
  body: string;
}) {
  return (
    <div className="flex flex-col gap-3 bg-background p-6">
      <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-[color:var(--accent-soft)] text-[color:var(--accent-strong)]">
        {icon}
      </div>
      <h3 className="font-display text-xl text-[color:var(--nav-brand-text)]">
        {title}
      </h3>
      <p className="text-[13.5px] leading-6 text-[color:var(--nav-link)]">
        {body}
      </p>
    </div>
  );
}

function Tag({ children }: { children: React.ReactNode }) {
  return (
    <span className="inline-flex items-center gap-1.5 rounded-full border border-[color:var(--nav-border)] bg-[color:var(--nav-shell)] px-3 py-1.5 text-[12px] font-medium text-[color:var(--nav-brand-text)]">
      <span className="h-1.5 w-1.5 rounded-full bg-[color:var(--accent)]" />
      {children}
    </span>
  );
}

function SpecCard({
  icon,
  title,
  lines,
  tone,
}: {
  icon: React.ReactNode;
  title: string;
  lines: string[];
  tone: string;
}) {
  return (
    <article className="group relative flex flex-col overflow-hidden rounded-2xl border border-[color:var(--nav-border)] bg-background p-5 transition hover:-translate-y-0.5 hover:shadow-[0_18px_50px_-32px_rgba(15,23,42,0.25)]">
      <span
        aria-hidden
        className="absolute -right-8 -top-8 h-24 w-24 rounded-full opacity-20 blur-2xl transition group-hover:opacity-40"
        style={{ background: tone }}
      />
      <div
        className="relative flex h-10 w-10 items-center justify-center rounded-xl"
        style={{ background: `${tone}1f`, color: tone }}
      >
        {icon}
      </div>
      <h3 className="relative mt-4 font-display text-2xl text-[color:var(--nav-brand-text)]">
        {title}
      </h3>
      <ul className="relative mt-3 space-y-2">
        {lines.map((line) => (
          <li
            key={line}
            className="flex gap-2 text-[13.5px] leading-6 text-[color:var(--nav-link)]"
          >
            <span
              className="mt-2 h-1 w-1 shrink-0 rounded-full"
              style={{ background: tone }}
            />
            {line}
          </li>
        ))}
      </ul>
    </article>
  );
}
