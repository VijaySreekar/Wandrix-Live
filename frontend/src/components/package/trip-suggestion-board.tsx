"use client";

import { useEffect, useState } from "react";
import { ArrowRight } from "lucide-react";

import { getLiveDestinationImage } from "@/components/package/trip-board-cards";
import { resolveDestinationSuggestionImage } from "@/lib/destination-images";
import { cn } from "@/lib/utils";
import type { PlannerBoardActionIntent } from "@/types/planner-board";
import type {
  AdvancedAnchorChoiceCard,
  DestinationSuggestionCard,
  PlanningModeChoiceCard,
  PlannerDecisionCard,
  TripSuggestionBoardState,
} from "@/types/trip-conversation";

type TripSuggestionBoardProps = {
  board: TripSuggestionBoardState;
  decisionCards: PlannerDecisionCard[];
  disabled: boolean;
  onAction: (action: PlannerBoardActionIntent) => void;
};

const BADGE_STYLES: Record<string, string> = {
  "top weather":
    "bg-[var(--planner-board-soft)] text-[var(--planner-board-accent-text)]",
  culture:
    "bg-[var(--planner-board-accent-soft)] text-[var(--planner-board-accent-text)]",
  history:
    "bg-[var(--planner-board-accent-soft)] text-[var(--planner-board-accent-text)]",
  nature:
    "bg-[var(--planner-board-soft)] text-[var(--planner-board-accent-text)]",
  shorthaul:
    "bg-[var(--planner-board-accent-soft)] text-[var(--planner-board-accent-text)]",
};

export function TripSuggestionBoard({
  board,
  decisionCards,
  disabled,
  onAction,
}: TripSuggestionBoardProps) {
  const cards = board.cards.slice(0, 4);
  const title = board.title?.trim() || "Sunny March Options";
  const subtitle =
    board.subtitle?.trim() || "Short-break recommendations for you";

  if (board.mode === "planning_mode_choice") {
    return (
      <section className="flex h-full flex-col bg-[var(--planner-board-bg)]">
        <div className="border-b border-[var(--planner-board-border)] px-8 py-8">
          <h2 className="font-display text-[2rem] font-bold tracking-[-0.03em] text-[var(--planner-board-title)]">
            {title}
          </h2>
          <p className="mt-2 max-w-2xl text-sm leading-7 text-[var(--planner-board-muted)]">
            {subtitle}
          </p>
        </div>

        <div className="flex-1 overflow-y-auto px-8 py-8">
          <div className="grid gap-4">
            {board.planning_mode_cards.map((card) => (
              <PlanningModeOptionCard
                key={card.id}
                card={card}
                disabled={disabled}
                onAction={onAction}
              />
            ))}
          </div>
        </div>
      </section>
    );
  }

  if (board.mode === "advanced_anchor_choice") {
    return (
      <section className="flex h-full flex-col bg-[var(--planner-board-bg)]">
        <div className="border-b border-[var(--planner-board-border)] px-8 py-8">
          <h2 className="font-display text-[2rem] font-bold tracking-[-0.03em] text-[var(--planner-board-title)]">
            {title}
          </h2>
          <p className="mt-2 max-w-2xl text-sm leading-7 text-[var(--planner-board-muted)]">
            {subtitle}
          </p>
        </div>

        <div className="flex-1 overflow-y-auto px-8 py-8">
          <div className="grid gap-4">
            {(board.advanced_anchor_cards ?? []).map((card) => (
              <AdvancedAnchorOptionCard
                key={card.id}
                card={card}
                disabled={disabled}
                onAction={onAction}
              />
            ))}
          </div>
        </div>
      </section>
    );
  }

  if (board.mode === "advanced_next_step") {
    return (
      <section className="flex h-full flex-col bg-[var(--planner-board-bg)]">
        <div className="border-b border-[var(--planner-board-border)] px-8 py-8">
          <h2 className="font-display text-[2rem] font-bold tracking-[-0.03em] text-[var(--planner-board-title)]">
            {title}
          </h2>
          <p className="mt-2 max-w-2xl text-sm leading-7 text-[var(--planner-board-muted)]">
            {subtitle}
          </p>
        </div>

        <div className="flex-1 overflow-y-auto px-8 py-8">
          <article className="rounded-[1.75rem] bg-[var(--planner-board-card)] px-6 py-6 shadow-[0_1px_1px_rgba(0,0,0,0.04),0_10px_24px_rgba(0,0,0,0.05)]">
            <h3 className="font-display text-lg font-bold text-[var(--planner-board-text)]">
              Guided planning is now active
            </h3>
            <p className="mt-2 text-sm leading-7 text-[var(--planner-board-muted)]">
              The shared trip brief is ready, so Wandrix will stay in guided mode
              instead of jumping straight into a quick itinerary draft.
            </p>
            <ul className="mt-5 space-y-3">
              {[
                "The first Advanced Planning anchor is now selected.",
                "That choice becomes the real branch between flights, stay, trip style, or activities.",
                "The current brief still stays editable in chat if you want to adjust it before the deeper flow begins.",
              ].map((bullet) => (
                <li
                  key={bullet}
                  className="flex items-start gap-3 text-sm leading-7 text-[var(--planner-board-muted)]"
                >
                  <span className="mt-2 block h-1.5 w-1.5 rounded-full bg-[color:var(--accent)]" />
                  <span>{bullet}</span>
                </li>
              ))}
            </ul>
          </article>
        </div>
      </section>
    );
  }

  if (board.mode === "decision_cards" && cards.length === 0) {
    return (
      <section className="flex h-full flex-col bg-[var(--planner-board-bg)]">
        <div className="px-8 pb-4 pt-8">
          <h2 className="font-display text-[2rem] font-bold tracking-[-0.03em] text-[var(--planner-board-title)]">
            {title}
          </h2>
          <p className="mt-1 text-sm text-[var(--planner-board-muted)]">{subtitle}</p>
        </div>
        <div className="flex-1 overflow-y-auto px-8 pb-10">
          <div className="space-y-4">
            {decisionCards.map((card) => (
              <article
                key={card.title}
                className="rounded-[1.75rem] bg-[var(--planner-board-card)] px-6 py-5 shadow-[0_1px_1px_rgba(0,0,0,0.04),0_10px_24px_rgba(0,0,0,0.05)]"
              >
                <h3 className="font-display text-lg font-bold text-[var(--planner-board-text)]">
                  {card.title}
                </h3>
                <p className="mt-2 text-sm leading-6 text-[var(--planner-board-muted)]">
                  {card.description}
                </p>
                <div className="mt-4 flex flex-wrap gap-2">
                  {card.options.map((option) => (
                    <span
                      key={option}
                      className="rounded-md bg-[var(--planner-board-soft)] px-3 py-1.5 text-xs font-semibold text-[var(--planner-board-muted)]"
                    >
                      {option}
                    </span>
                  ))}
                </div>
              </article>
            ))}
          </div>
        </div>
      </section>
    );
  }

  return (
    <section className="flex h-full flex-col bg-[var(--planner-board-bg)]">
      <div className="px-8 pb-4 pt-8">
        <h2 className="font-display text-[2rem] font-bold tracking-[-0.03em] text-[var(--planner-board-title)]">
          {title}
        </h2>
        <p className="mt-1 text-sm text-[var(--planner-board-muted)]">{subtitle}</p>
        {board.source_context ? (
          <p className="mt-3 max-w-xl text-sm leading-6 text-[var(--planner-board-muted)]">
            {board.source_context}
          </p>
        ) : null}
      </div>

      <div className="flex-1 overflow-y-auto px-8 pb-10">
        <div className="grid grid-cols-1 gap-6 xl:grid-cols-2">
          {cards.map((card) => (
            <DestinationSuggestionOption
              key={card.id}
              card={card}
              disabled={disabled}
              onAction={onAction}
            />
          ))}
        </div>

        <button
          type="button"
          disabled={disabled}
          onClick={() =>
            onAction({
              action_id: crypto.randomUUID(),
              type: "own_choice",
              prompt_text:
                board.own_choice_prompt ||
                "Tell me the destination you already have in mind.",
            })
          }
          className={cn(
            "mt-6 flex w-full items-center justify-between rounded-[1.75rem] border border-[var(--planner-board-border)] bg-[var(--planner-board-card)] px-6 py-5 text-left shadow-[0_1px_1px_rgba(0,0,0,0.04),0_10px_24px_rgba(0,0,0,0.05)] transition-colors duration-150",
            disabled
              ? "cursor-wait opacity-70"
              : "hover:border-[var(--planner-board-border)] hover:bg-[var(--planner-board-card-hover)]",
          )}
        >
          <div>
            <p className="font-display text-lg font-bold text-[var(--planner-board-text)]">
              Use your own destination
            </p>
            <p className="mt-1 text-sm leading-6 text-[var(--planner-board-muted)]">
              Already have somewhere in mind? Type it in chat and Wandrix will
              shape the trip around it.
            </p>
          </div>
          <ArrowRight className="h-5 w-5 shrink-0 text-[var(--planner-board-cta)]" />
        </button>
      </div>
    </section>
  );
}

function PlanningModeOptionCard({
  card,
  disabled,
  onAction,
}: {
  card: PlanningModeChoiceCard;
  disabled: boolean;
  onAction: (action: PlannerBoardActionIntent) => void;
}) {
  const isDisabled = disabled || card.status !== "available";

  return (
    <article
      className={cn(
        "rounded-xl border bg-[var(--planner-board-card)] px-6 py-6 shadow-[0_1px_1px_rgba(0,0,0,0.04),0_8px_18px_rgba(0,0,0,0.04)]",
        card.status === "in_development"
          ? "border-[color:color-mix(in_srgb,var(--planner-board-border)_76%,transparent)]"
          : "border-[var(--planner-board-border)]",
      )}
    >
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h3 className="font-display text-xl font-bold tracking-[-0.02em] text-[var(--planner-board-text)]">
            {card.title}
          </h3>
          <p className="mt-2 max-w-xl text-sm leading-7 text-[var(--planner-board-muted)]">
            {card.description}
          </p>
        </div>
        {card.badge ? (
          <span
            className={cn(
              "rounded-md border px-2.5 py-1 text-[11px] font-semibold uppercase tracking-[0.14em]",
              card.status === "available"
                ? "border-[color:color-mix(in_srgb,var(--accent)_24%,transparent)] bg-[color:color-mix(in_srgb,var(--accent)_10%,transparent)] text-[color:var(--accent)]"
                : "border-[var(--planner-board-border)] bg-[var(--planner-board-soft)] text-[var(--planner-board-muted-strong)]",
            )}
          >
            {card.badge}
          </span>
        ) : null}
      </div>

      <ul className="mt-5 space-y-3">
        {card.bullets.map((bullet) => (
          <li
            key={bullet}
            className="flex items-start gap-3 text-sm leading-7 text-[var(--planner-board-muted)]"
          >
            <span
              className={cn(
                "mt-2 block h-1.5 w-1.5 rounded-full",
                card.status === "available"
                  ? "bg-[color:var(--accent)]"
                  : "bg-[var(--planner-board-muted-strong)]",
              )}
            />
            <span>{bullet}</span>
          </li>
        ))}
      </ul>

      <div className="mt-6">
        <button
          type="button"
          disabled={isDisabled}
          onClick={() =>
            onAction({
              action_id: crypto.randomUUID(),
              type:
                card.id === "quick" ? "select_quick_plan" : "select_advanced_plan",
            })
          }
          className={cn(
            "inline-flex items-center rounded-lg border px-4 py-2.5 text-sm font-semibold transition-colors",
            isDisabled
              ? "cursor-not-allowed border-[var(--planner-board-border)] bg-[var(--planner-board-soft)] text-[var(--planner-board-muted-strong)]"
              : "border-[color:var(--accent)] bg-[color:var(--accent)] text-[color:var(--accent-foreground)] hover:bg-[color:color-mix(in_srgb,var(--accent)_92%,black)]",
          )}
        >
          {card.cta_label || "Continue"}
        </button>
      </div>
    </article>
  );
}

function AdvancedAnchorOptionCard({
  card,
  disabled,
  onAction,
}: {
  card: AdvancedAnchorChoiceCard;
  disabled: boolean;
  onAction: (action: PlannerBoardActionIntent) => void;
}) {
  return (
    <article className="rounded-xl border border-[var(--planner-board-border)] bg-[var(--planner-board-card)] px-6 py-6 shadow-[0_1px_1px_rgba(0,0,0,0.04),0_8px_18px_rgba(0,0,0,0.04)]">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h3 className="font-display text-xl font-bold tracking-[-0.02em] text-[var(--planner-board-text)]">
            {card.title}
          </h3>
          <p className="mt-2 max-w-xl text-sm leading-7 text-[var(--planner-board-muted)]">
            {card.description}
          </p>
        </div>
        {card.badge ? (
          <span className="rounded-md border border-[color:color-mix(in_srgb,var(--accent)_24%,transparent)] bg-[color:color-mix(in_srgb,var(--accent)_10%,transparent)] px-2.5 py-1 text-[11px] font-semibold uppercase tracking-[0.14em] text-[color:var(--accent)]">
            {card.badge}
          </span>
        ) : null}
      </div>

      <ul className="mt-5 space-y-3">
        {card.bullets.map((bullet) => (
          <li
            key={bullet}
            className="flex items-start gap-3 text-sm leading-7 text-[var(--planner-board-muted)]"
          >
            <span
              className={cn(
                "mt-2 block h-1.5 w-1.5 rounded-full",
                card.recommended
                  ? "bg-[color:var(--accent)]"
                  : "bg-[var(--planner-board-muted-strong)]",
              )}
            />
            <span>{bullet}</span>
          </li>
        ))}
      </ul>

      <div className="mt-6">
        <button
          type="button"
          disabled={disabled}
          onClick={() =>
            onAction({
              action_id: crypto.randomUUID(),
              type: "select_advanced_anchor",
              advanced_anchor: card.id,
            })
          }
          className={cn(
            "inline-flex items-center rounded-lg border px-4 py-2.5 text-sm font-semibold transition-colors",
            disabled
              ? "cursor-not-allowed border-[var(--planner-board-border)] bg-[var(--planner-board-soft)] text-[var(--planner-board-muted-strong)]"
              : "border-[color:var(--accent)] bg-[color:var(--accent)] text-[color:var(--accent-foreground)] hover:bg-[color:color-mix(in_srgb,var(--accent)_92%,black)]",
          )}
        >
          {card.cta_label || "Choose anchor"}
        </button>
      </div>
    </article>
  );
}

function badgeLabel(card: DestinationSuggestionCard) {
  const label = card.practicality_label?.trim();
  if (label) {
    return label;
  }

  const text = card.short_reason.toLowerCase();
  if (text.includes("museum") || text.includes("culture") || text.includes("tapas")) {
    return "Culture";
  }
  if (text.includes("historic") || text.includes("fortress")) {
    return "History";
  }
  if (text.includes("hike") || text.includes("volcanic") || text.includes("island")) {
    return "Nature";
  }

  return "Shorthaul";
}

function badgeClassName(card: DestinationSuggestionCard) {
  const normalized = badgeLabel(card).toLowerCase();
  return BADGE_STYLES[normalized] ?? "bg-[var(--planner-board-accent-soft)] text-[var(--planner-board-accent-text)]";
}

function DestinationSuggestionOption({
  card,
  disabled,
  onAction,
}: {
  card: DestinationSuggestionCard;
  disabled: boolean;
  onAction: (action: PlannerBoardActionIntent) => void;
}) {
  const [resolvedImage, setResolvedImage] = useState(() =>
    getLiveDestinationImage(card.destination_name),
  );

  useEffect(() => {
    let cancelled = false;

    async function loadImage() {
      const image = await resolveDestinationSuggestionImage(card);
      if (!cancelled && image) {
        setResolvedImage(image);
      }
    }

    void loadImage();

    return () => {
      cancelled = true;
    };
  }, [card]);

  return (
    <button
      type="button"
      disabled={disabled}
      onClick={() => {
        onAction({
          action_id: crypto.randomUUID(),
          type: "select_destination_suggestion",
          destination_name: card.destination_name,
          country_or_region: card.country_or_region,
          suggestion_id: card.id,
        });
      }}
      className={cn(
        "group flex h-full cursor-pointer flex-col overflow-hidden rounded-[1.75rem] bg-[var(--planner-board-card)] text-left shadow-[0_1px_1px_rgba(0,0,0,0.04),0_10px_24px_rgba(0,0,0,0.05)] transition-[transform,box-shadow,background-color] duration-200",
        disabled
          ? "cursor-wait opacity-70"
          : "hover:-translate-y-0.5 hover:bg-[var(--planner-board-card-hover)] hover:shadow-[0_1px_1px_rgba(0,0,0,0.04),0_16px_30px_rgba(0,0,0,0.08)]",
      )}
    >
      <div className="h-44 overflow-hidden bg-[var(--planner-board-soft)]">
        <img
          src={resolvedImage}
          alt={card.destination_name}
          className="h-full w-full object-cover transition-transform duration-700 group-hover:scale-[1.04]"
        />
      </div>
      <div className="flex flex-1 flex-col p-6">
        <div className="mb-2 flex items-center gap-2">
          <span
            className={cn(
              "rounded px-2 py-0.5 text-[10px] font-bold uppercase tracking-[0.16em]",
              badgeClassName(card),
            )}
          >
            {badgeLabel(card)}
          </span>
          <span className="text-xs text-[var(--planner-board-muted-strong)]">{card.country_or_region}</span>
        </div>
        <h3 className="font-display text-[1.8rem] font-bold leading-none tracking-[-0.03em] text-[var(--planner-board-text)]">
          {card.destination_name}
        </h3>
        <p className="mb-6 mt-3 flex-1 text-sm leading-7 text-[var(--planner-board-muted)]">
          {card.short_reason}
        </p>
        <span className="inline-flex items-center gap-2 text-sm font-bold text-[var(--planner-board-cta)]">
          Explore this
          <ArrowRight className="h-4 w-4" />
        </span>
      </div>
    </button>
  );
}
