import {
  ArrowUp,
  CalendarDays,
  Compass,
  MapPin,
  Mic,
  Paperclip,
  Plane,
  Plus,
  Search,
  SendHorizontal,
  Sparkles,
  SquarePen,
  type LucideIcon,
} from "lucide-react";

type ChatBarSample = {
  id: string;
  name: string;
  description: string;
  text: string;
  shellClassName: string;
  bodyClassName: string;
  inputClassName: string;
  sendClassName: string;
  iconClassName: string;
  icon: LucideIcon;
  sendIcon: "arrow" | "send";
  rows?: number;
  prefix?: string;
  utilityIcons?: LucideIcon[];
};

const samples: ChatBarSample[] = [
  {
    id: "01",
    name: "Soft Glass Dock",
    description: "Single calm surface, subtle border, round embedded send.",
    text: "Plan a slow food weekend in Lisbon for early autumn",
    shellClassName:
      "rounded-[1.55rem] border border-[color:var(--chat-rail-border)] bg-[color:color-mix(in_srgb,var(--chat-rail-surface-strong)_82%,transparent)] p-[1px] shadow-[var(--chat-shadow-soft)] backdrop-blur-xl",
    bodyClassName:
      "min-h-[4.75rem] rounded-[1.45rem] bg-[color:var(--chat-rail-surface-strong)] px-4 py-3",
    inputClassName:
      "text-[0.96rem] leading-6 text-foreground placeholder:text-muted-foreground",
    sendClassName:
      "h-11 w-11 rounded-full border border-[color:color-mix(in_srgb,var(--accent)_28%,transparent)] bg-[linear-gradient(135deg,var(--accent),var(--accent2))] text-[color:var(--chat-composer-on-accent)] shadow-[var(--chat-shadow-card)]",
    iconClassName:
      "h-10 w-10 rounded-full border border-[color:var(--chat-rail-border)] bg-[color:color-mix(in_srgb,var(--accent)_9%,var(--chat-rail-surface-strong))] text-[color:var(--accent)]",
    icon: Sparkles,
    sendIcon: "arrow",
  },
  {
    id: "02",
    name: "Travel Note",
    description: "A warmer, journal-like bar with a compact send chip.",
    text: "I want somewhere coastal, warm, and easy from London",
    shellClassName:
      "rounded-[1.15rem] border border-[color:var(--nav-border)] bg-[color:var(--nav-shell)] p-2 shadow-[var(--nav-shadow)]",
    bodyClassName:
      "min-h-[4.25rem] rounded-[0.95rem] bg-[color:var(--nav-shell-strong)] px-3.5 py-3",
    inputClassName:
      "text-[0.95rem] leading-6 text-[color:var(--nav-link)] placeholder:text-muted-foreground",
    sendClassName:
      "h-10 min-w-20 rounded-full border border-[color:var(--nav-border-strong)] bg-[color:var(--nav-active-bg)] px-4 text-[color:var(--nav-active-text)] shadow-[var(--chat-shadow-card)]",
    iconClassName:
      "h-9 w-9 rounded-lg border border-[color:var(--nav-border)] bg-[color:var(--nav-brand-chip-bg)] text-[color:var(--nav-brand-mark)]",
    icon: SquarePen,
    sendIcon: "send",
    prefix: "Ask",
  },
  {
    id: "03",
    name: "Planner Capsule",
    description: "Dense and tidy, suited to long planning sessions.",
    text: "Compare Kyoto and Seoul for seven nights with great food",
    shellClassName:
      "rounded-full border border-[color:var(--chat-rail-border-strong)] bg-[color:var(--chat-rail-surface-strong)] px-3 py-2 shadow-[var(--chat-shadow-soft)]",
    bodyClassName: "min-h-14 rounded-full px-1",
    inputClassName:
      "text-[0.94rem] leading-6 text-foreground placeholder:text-muted-foreground",
    sendClassName:
      "h-10 w-10 rounded-full bg-[color:var(--planner-board-cta)] text-[color:var(--chat-composer-on-accent)] shadow-[var(--chat-shadow-card)]",
    iconClassName:
      "h-10 w-10 rounded-full bg-[color:var(--planner-board-accent-soft)] text-[color:var(--planner-board-title)]",
    icon: Compass,
    sendIcon: "arrow",
  },
  {
    id: "04",
    name: "Itinerary Rail",
    description: "A little more structured, with quick utility controls.",
    text: "Build a 5-day city break with flights, hotel, and galleries",
    shellClassName:
      "rounded-[1.25rem] border border-[color:var(--chat-rail-border)] bg-[color:var(--chat-rail-surface)] p-2 shadow-[var(--chat-shadow-soft)]",
    bodyClassName:
      "min-h-[4.5rem] rounded-[1rem] bg-[color:var(--chat-rail-surface-strong)] px-3 py-3",
    inputClassName:
      "text-[0.95rem] leading-6 text-foreground placeholder:text-muted-foreground",
    sendClassName:
      "h-10 w-10 rounded-xl border border-[color:color-mix(in_srgb,var(--accent)_20%,transparent)] bg-[color:var(--accent)] text-[color:var(--chat-composer-on-accent)]",
    iconClassName:
      "h-9 w-9 rounded-xl border border-[color:var(--chat-rail-border)] bg-[color:var(--chat-rail-control-bg)] text-[color:var(--accent)]",
    icon: CalendarDays,
    sendIcon: "send",
    utilityIcons: [Paperclip, Mic],
  },
  {
    id: "05",
    name: "First-Class Dock",
    description: "More premium and spacious, with a polished command feel.",
    text: "Find a special anniversary trip with calm hotels and standout dinners",
    shellClassName:
      "rounded-[1.7rem] border border-[color:var(--planner-board-border)] bg-[linear-gradient(135deg,var(--planner-board-card),var(--planner-board-soft))] p-[1px] shadow-[var(--glass-shadow)]",
    bodyClassName:
      "min-h-[5rem] rounded-[1.6rem] bg-[color:var(--planner-board-card)] px-4 py-3.5",
    inputClassName:
      "text-[0.98rem] leading-6 text-[color:var(--planner-board-text)] placeholder:text-[color:var(--planner-board-muted)]",
    sendClassName:
      "h-12 w-12 rounded-2xl bg-[color:var(--planner-board-cta)] text-[color:var(--chat-composer-on-accent)] shadow-[var(--chat-shadow-card)]",
    iconClassName:
      "h-11 w-11 rounded-2xl bg-[color:var(--planner-board-accent-soft)] text-[color:var(--planner-board-title)]",
    icon: Plane,
    sendIcon: "arrow",
  },
  {
    id: "06",
    name: "Quiet Command",
    description: "Minimal but not bare: light chrome, strong affordance.",
    text: "Help me pick between Rome, Florence, and Naples",
    shellClassName:
      "rounded-[1rem] border border-[color:var(--chat-rail-border-strong)] bg-[color:var(--chat-rail-surface-strong)] p-2 shadow-[var(--chat-shadow-card)]",
    bodyClassName:
      "min-h-[4.25rem] rounded-[0.8rem] bg-[color:var(--chat-pane-bg)] px-3 py-3",
    inputClassName:
      "text-[0.95rem] leading-6 text-foreground placeholder:text-muted-foreground",
    sendClassName:
      "h-10 w-10 rounded-lg bg-foreground text-background",
    iconClassName:
      "h-9 w-9 rounded-lg bg-[color:var(--chat-rail-surface-strong)] text-muted-foreground ring-1 ring-[color:var(--chat-rail-border)]",
    icon: Search,
    sendIcon: "arrow",
  },
  {
    id: "07",
    name: "Board-Aligned",
    description: "Uses the live board visual language for tighter cohesion.",
    text: "Turn this into an editable quick plan before we book anything",
    shellClassName:
      "rounded-[1.3rem] border border-[color:var(--planner-board-border)] bg-[color:var(--planner-board-bg)] p-2 shadow-[var(--chat-shadow-soft)]",
    bodyClassName:
      "min-h-[4.6rem] rounded-[1.05rem] bg-[color:var(--planner-board-card)] px-3.5 py-3",
    inputClassName:
      "text-[0.95rem] leading-6 text-[color:var(--planner-board-text)] placeholder:text-[color:var(--planner-board-muted)]",
    sendClassName:
      "h-10 w-10 rounded-full bg-[color:var(--planner-board-cta)] text-[color:var(--chat-composer-on-accent)]",
    iconClassName:
      "h-9 w-9 rounded-full bg-[color:var(--planner-board-accent-soft)] text-[color:var(--planner-board-title)]",
    icon: MapPin,
    sendIcon: "send",
  },
  {
    id: "08",
    name: "Assistant Glow",
    description: "Soft branded focus without the heavy bordered textarea.",
    text: "Make this trip feel slower, greener, and less touristy",
    shellClassName:
      "rounded-[1.55rem] border border-[color:color-mix(in_srgb,var(--accent)_18%,var(--chat-rail-border))] bg-[color:color-mix(in_srgb,var(--accent)_5%,var(--chat-rail-surface-strong))] p-[1px] shadow-[var(--chat-shadow-soft)]",
    bodyClassName:
      "min-h-[4.75rem] rounded-[1.45rem] bg-[color:var(--chat-rail-surface-strong)] px-4 py-3",
    inputClassName:
      "text-[0.96rem] leading-6 text-foreground placeholder:text-muted-foreground",
    sendClassName:
      "h-11 w-11 rounded-full bg-[color:var(--accent-strong)] text-[color:var(--chat-composer-on-accent)] shadow-[var(--chat-shadow-card)]",
    iconClassName:
      "h-10 w-10 rounded-full bg-[color:var(--accent-soft)] text-[color:var(--accent)]",
    icon: Sparkles,
    sendIcon: "arrow",
  },
  {
    id: "09",
    name: "Compact Concierge",
    description: "A crisp pill with small add and voice tools.",
    text: "Add a weather-aware plan B for rainy afternoons",
    shellClassName:
      "rounded-full border border-[color:var(--chat-rail-border)] bg-[color:var(--chat-rail-surface-strong)] px-2.5 py-2 shadow-[var(--chat-shadow-soft)]",
    bodyClassName: "min-h-14 rounded-full px-1",
    inputClassName:
      "text-[0.94rem] leading-6 text-foreground placeholder:text-muted-foreground",
    sendClassName:
      "h-10 w-10 rounded-full bg-[linear-gradient(135deg,var(--accent),var(--accent2))] text-[color:var(--chat-composer-on-accent)]",
    iconClassName:
      "h-9 w-9 rounded-full border border-[color:var(--chat-rail-border)] bg-[color:var(--chat-rail-control-bg)] text-muted-foreground",
    icon: Plus,
    sendIcon: "arrow",
    utilityIcons: [Mic],
  },
  {
    id: "10",
    name: "Brochure Draft",
    description: "Wider, editorial, and good for longer final-plan prompts.",
    text: "Write the plan in a polished brochure style, but keep it editable",
    shellClassName:
      "rounded-[1.2rem] border border-[color:var(--nav-border)] bg-[color:var(--nav-shell)] p-2 shadow-[var(--chat-shadow-soft)]",
    bodyClassName:
      "min-h-[5.3rem] rounded-[0.95rem] bg-[color:var(--nav-shell-strong)] px-4 py-3.5",
    inputClassName:
      "text-[0.98rem] leading-7 text-[color:var(--nav-link)] placeholder:text-muted-foreground",
    sendClassName:
      "h-11 w-11 rounded-xl bg-[color:var(--nav-brand-mark)] text-[color:var(--chat-composer-on-accent)]",
    iconClassName:
      "h-10 w-10 rounded-xl bg-[color:var(--nav-active-bg)] text-[color:var(--nav-brand-mark)]",
    icon: SquarePen,
    sendIcon: "send",
    rows: 2,
  },
  {
    id: "11",
    name: "Floating Planner",
    description: "Airier and more modern, with strong separation from the page.",
    text: "I have 6 nights and want a stylish but not frantic trip",
    shellClassName:
      "rounded-[1.8rem] border border-[color:var(--glass-border)] bg-[color:var(--glass-panel-strong)] p-3 shadow-[var(--glass-shadow)] backdrop-blur-2xl",
    bodyClassName:
      "min-h-[4.85rem] rounded-[1.5rem] bg-[color:var(--chat-rail-surface-strong)] px-3.5 py-3",
    inputClassName:
      "text-[0.96rem] leading-6 text-foreground placeholder:text-muted-foreground",
    sendClassName:
      "h-11 w-11 rounded-full border border-[color:var(--chat-rail-border)] bg-[color:var(--accent)] text-[color:var(--chat-composer-on-accent)]",
    iconClassName:
      "h-10 w-10 rounded-full bg-[color:var(--chat-rail-control-bg)] text-[color:var(--accent)]",
    icon: Compass,
    sendIcon: "arrow",
  },
  {
    id: "12",
    name: "Slim Split",
    description: "A narrower command-line treatment for dense chat layouts.",
    text: "Keep the hotel central and activities walkable",
    shellClassName:
      "rounded-xl border border-[color:var(--chat-rail-border-strong)] bg-[color:var(--chat-rail-surface-strong)] p-1.5 shadow-[var(--chat-shadow-card)]",
    bodyClassName:
      "min-h-[3.65rem] rounded-lg bg-[color:var(--chat-rail-control-bg)] px-2.5 py-2",
    inputClassName:
      "text-[0.92rem] leading-6 text-foreground placeholder:text-muted-foreground",
    sendClassName:
      "h-9 w-9 rounded-lg bg-[color:var(--accent)] text-[color:var(--chat-composer-on-accent)]",
    iconClassName:
      "h-9 w-9 rounded-lg text-[color:var(--accent)]",
    icon: Search,
    sendIcon: "send",
  },
  {
    id: "13",
    name: "Layered Studio",
    description: "More depth, still composed enough for the main chat.",
    text: "Start broad, ask me clarifying questions, and avoid booking assumptions",
    shellClassName:
      "rounded-[1.4rem] border border-[color:var(--chat-rail-border)] bg-[color:var(--chat-rail-surface)] p-2.5 shadow-[var(--chat-shadow-soft)]",
    bodyClassName:
      "min-h-[4.9rem] rounded-[1.1rem] border border-[color:var(--chat-rail-border)] bg-[color:var(--chat-rail-surface-strong)] px-3.5 py-3",
    inputClassName:
      "text-[0.96rem] leading-6 text-foreground placeholder:text-muted-foreground",
    sendClassName:
      "h-11 w-11 rounded-2xl bg-[linear-gradient(135deg,var(--accent-strong),var(--accent))] text-[color:var(--chat-composer-on-accent)]",
    iconClassName:
      "h-10 w-10 rounded-2xl bg-[color:var(--chat-rail-control-bg)] text-[color:var(--accent)] ring-1 ring-[color:var(--chat-rail-border)]",
    icon: Sparkles,
    sendIcon: "arrow",
    utilityIcons: [Paperclip],
  },
  {
    id: "14",
    name: "Trip Board Dock",
    description: "A practical bar that visually belongs with board actions.",
    text: "Confirm the destination, then show me flights and stays next",
    shellClassName:
      "rounded-[1.05rem] border border-[color:var(--planner-board-border)] bg-[color:var(--planner-board-card)] p-2 shadow-[var(--chat-shadow-card)]",
    bodyClassName:
      "min-h-[4.4rem] rounded-[0.8rem] bg-[color:var(--planner-board-soft)] px-3 py-3",
    inputClassName:
      "text-[0.95rem] leading-6 text-[color:var(--planner-board-text)] placeholder:text-[color:var(--planner-board-muted)]",
    sendClassName:
      "h-10 min-w-16 rounded-lg bg-[color:var(--planner-board-cta)] px-3 text-[color:var(--chat-composer-on-accent)]",
    iconClassName:
      "h-9 w-9 rounded-lg bg-[color:var(--planner-board-card)] text-[color:var(--planner-board-title)] ring-1 ring-[color:var(--planner-board-border)]",
    icon: CalendarDays,
    sendIcon: "send",
    prefix: "Send",
  },
  {
    id: "15",
    name: "Premium Minimal",
    description: "The cleanest option, with just enough warmth and depth.",
    text: "Plan something memorable, not overpacked",
    shellClassName:
      "rounded-[1.35rem] border border-[color:var(--chat-rail-border)] bg-[color:var(--chat-rail-surface-strong)] p-2 shadow-[var(--chat-shadow-soft)]",
    bodyClassName:
      "min-h-[4.5rem] rounded-[1.1rem] px-3 py-3",
    inputClassName:
      "text-[0.96rem] leading-6 text-foreground placeholder:text-muted-foreground",
    sendClassName:
      "h-11 w-11 rounded-full border border-[color:var(--chat-rail-border)] bg-foreground text-background",
    iconClassName:
      "h-10 w-10 rounded-full text-muted-foreground",
    icon: Compass,
    sendIcon: "arrow",
  },
];

export default function ChatBarPreviewsPage() {
  return (
    <main className="min-h-[calc(100vh-var(--nav-height))] bg-[color:var(--chat-pane-bg)] px-4 py-8 text-foreground sm:px-8">
      <div className="mx-auto flex w-full max-w-7xl flex-col gap-7">
        <header className="flex flex-col gap-3 border-b border-[color:var(--chat-rail-border)] pb-6">
          <div className="text-xs font-medium uppercase tracking-[0.22em] text-[color:var(--accent)]">
            Chat bar previews
          </div>
          <div className="flex flex-col gap-3 lg:flex-row lg:items-end lg:justify-between">
            <div>
              <h1 className="text-3xl font-semibold tracking-normal text-foreground sm:text-4xl">
                Choose a Wandrix composer direction
              </h1>
              <p className="mt-2 max-w-2xl text-sm leading-6 text-muted-foreground">
                Pick a sample number and I can integrate that treatment into the real chat composer.
              </p>
            </div>
            <div className="inline-flex w-fit rounded-full border border-[color:var(--chat-rail-border)] bg-[color:var(--chat-rail-surface-strong)] px-3 py-1.5 text-sm text-muted-foreground">
              15 options
            </div>
          </div>
        </header>

        <section className="grid gap-4 xl:grid-cols-2">
          {samples.map((sample) => (
            <ChatBarPreviewCard key={sample.id} sample={sample} />
          ))}
        </section>
      </div>
    </main>
  );
}

function ChatBarPreviewCard({ sample }: { sample: ChatBarSample }) {
  return (
    <article className="rounded-[1.15rem] border border-[color:var(--chat-rail-border)] bg-[color:var(--chat-rail-surface)] p-4 shadow-[var(--chat-shadow-soft)]">
      <div className="mb-4 flex items-start justify-between gap-4">
        <div>
          <div className="text-xs font-medium uppercase tracking-[0.18em] text-[color:var(--accent)]">
            Sample {sample.id}
          </div>
          <h2 className="mt-1 text-base font-semibold text-foreground">
            {sample.name}
          </h2>
          <p className="mt-1 text-sm leading-6 text-muted-foreground">
            {sample.description}
          </p>
        </div>
      </div>

      <div className={sample.shellClassName}>
        <div className={`flex items-end gap-2 ${sample.bodyClassName}`}>
          <IconShell className={sample.iconClassName} icon={sample.icon} />
          <div className="min-w-0 flex-1">
            <textarea
              readOnly
              rows={sample.rows ?? 1}
              defaultValue={sample.text}
              className={`block max-h-28 min-h-10 w-full resize-none overflow-hidden bg-transparent py-2 outline-none ${sample.inputClassName}`}
            />
          </div>
          {sample.utilityIcons?.map((Icon, iconIndex) => (
            <button
              key={`${sample.id}-${iconIndex}`}
              type="button"
              aria-label="Preview utility"
              className="mb-0.5 hidden h-10 w-10 shrink-0 items-center justify-center rounded-full text-muted-foreground transition-colors hover:text-foreground sm:flex"
            >
              <Icon className="h-4 w-4" />
            </button>
          ))}
          <button
            type="button"
            aria-label={`Choose ${sample.name}`}
            className={`mb-0.5 inline-flex shrink-0 items-center justify-center gap-2 text-sm font-medium transition-transform hover:-translate-y-0.5 ${sample.sendClassName}`}
          >
            {sample.prefix ? <span>{sample.prefix}</span> : null}
            {sample.sendIcon === "send" ? (
              <SendHorizontal className="h-4 w-4" />
            ) : (
              <ArrowUp className="h-4 w-4" />
            )}
          </button>
        </div>
      </div>
    </article>
  );
}

function IconShell({
  className,
  icon: Icon,
}: {
  className: string;
  icon: LucideIcon;
}) {
  return (
    <span
      aria-hidden="true"
      className={`mb-0.5 hidden shrink-0 items-center justify-center sm:inline-flex ${className}`}
    >
      <Icon className="h-4 w-4" />
    </span>
  );
}
