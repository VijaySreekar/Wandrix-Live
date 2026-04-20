"use client";

import { useEffect, useState } from "react";
import { ArrowRight } from "lucide-react";

import { getLiveDestinationImage } from "@/components/package/trip-board-cards";
import { resolveDestinationSuggestionImage } from "@/lib/destination-images";
import { cn } from "@/lib/utils";
import type { PlannerBoardActionIntent } from "@/types/planner-board";
import type {
  DestinationSuggestionCard,
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
