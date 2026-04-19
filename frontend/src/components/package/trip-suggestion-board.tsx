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
    "bg-[#ffe5db] text-[#72361b]",
  culture:
    "bg-[#c5e6e1] text-[#305651]",
  history:
    "bg-[#d9f0ec] text-[#244742]",
  nature:
    "bg-[#e9efd4] text-[#446037]",
  shorthaul:
    "bg-[#d9f0ec] text-[#244742]",
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
      <section className="flex h-full flex-col bg-[#f3f4f4]">
        <div className="px-8 pb-4 pt-8">
          <h2 className="font-display text-[2rem] font-bold tracking-[-0.03em] text-[#155e59]">
            {title}
          </h2>
          <p className="mt-1 text-sm text-[#687270]">{subtitle}</p>
        </div>
        <div className="flex-1 overflow-y-auto px-8 pb-10">
          <div className="space-y-4">
            {decisionCards.map((card) => (
              <article
                key={card.title}
                className="rounded-[1.75rem] bg-white px-6 py-5 shadow-[0_1px_1px_rgba(0,0,0,0.04),0_10px_24px_rgba(0,0,0,0.05)]"
              >
                <h3 className="font-display text-lg font-bold text-[#182322]">
                  {card.title}
                </h3>
                <p className="mt-2 text-sm leading-6 text-[#626b68]">
                  {card.description}
                </p>
                <div className="mt-4 flex flex-wrap gap-2">
                  {card.options.map((option) => (
                    <span
                      key={option}
                      className="rounded-md bg-[#f2f4f3] px-3 py-1.5 text-xs font-semibold text-[#4f5b58]"
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
    <section className="flex h-full flex-col bg-[#f3f4f4]">
      <div className="px-8 pb-4 pt-8">
        <h2 className="font-display text-[2rem] font-bold tracking-[-0.03em] text-[#155e59]">
          {title}
        </h2>
        <p className="mt-1 text-sm text-[#687270]">{subtitle}</p>
        {board.source_context ? (
          <p className="mt-3 max-w-xl text-sm leading-6 text-[#5c6663]">
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
            "mt-6 flex w-full items-center justify-between rounded-[1.75rem] border border-[#d7dddb] bg-white px-6 py-5 text-left shadow-[0_1px_1px_rgba(0,0,0,0.04),0_10px_24px_rgba(0,0,0,0.05)] transition-colors duration-150",
            disabled
              ? "cursor-wait opacity-70"
              : "hover:border-[#bfd1cc] hover:bg-[#fbfcfc]",
          )}
        >
          <div>
            <p className="font-display text-lg font-bold text-[#182322]">
              Use your own destination
            </p>
            <p className="mt-1 text-sm leading-6 text-[#626b68]">
              Already have somewhere in mind? Type it in chat and Wandrix will
              shape the trip around it.
            </p>
          </div>
          <ArrowRight className="h-5 w-5 shrink-0 text-[#0d6c65]" />
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
  return BADGE_STYLES[normalized] ?? "bg-[#d9f0ec] text-[#244742]";
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
        "group flex h-full cursor-pointer flex-col overflow-hidden rounded-[1.75rem] bg-white text-left shadow-[0_1px_1px_rgba(0,0,0,0.04),0_10px_24px_rgba(0,0,0,0.05)] transition-[transform,box-shadow] duration-200",
        disabled
          ? "cursor-wait opacity-70"
          : "hover:-translate-y-0.5 hover:shadow-[0_1px_1px_rgba(0,0,0,0.04),0_16px_30px_rgba(0,0,0,0.08)]",
      )}
    >
      <div className="h-44 overflow-hidden bg-[#eef2f1]">
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
          <span className="text-xs text-[#7a8381]">{card.country_or_region}</span>
        </div>
        <h3 className="font-display text-[1.8rem] font-bold leading-none tracking-[-0.03em] text-[#182322]">
          {card.destination_name}
        </h3>
        <p className="mb-6 mt-3 flex-1 text-sm leading-7 text-[#626b68]">
          {card.short_reason}
        </p>
        <span className="inline-flex items-center gap-2 text-sm font-bold text-[#0d6c65]">
          Explore this
          <ArrowRight className="h-4 w-4" />
        </span>
      </div>
    </button>
  );
}
