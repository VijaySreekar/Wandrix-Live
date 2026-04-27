"use client";

import { useEffect, useState } from "react";
import Image from "next/image";
import { ArrowRight } from "lucide-react";

import {
  getDestinationSuggestionImageFallback,
  getDestinationSuggestionImagePreview,
  resolveDestinationSuggestionImage,
} from "@/lib/destination-images";
import { cn } from "@/lib/utils";
import type { PlannerBoardActionIntent } from "@/types/planner-board";
import type { DestinationSuggestionCard } from "@/types/trip-conversation";

const BADGE_STYLES: Record<string, string> = {
  culture:
    "bg-[var(--planner-board-accent-soft)] text-[var(--planner-board-accent-text)]",
  history:
    "bg-[var(--planner-board-soft)] text-[var(--planner-board-title)]",
  nature:
    "bg-[var(--planner-board-soft)] text-[var(--planner-board-accent-text)]",
  shorthaul:
    "bg-[var(--planner-board-accent-soft)] text-[var(--planner-board-accent-text)]",
};

type DestinationDiscoveryCardProps = {
  card: DestinationSuggestionCard;
  compact?: boolean;
  disabled: boolean;
  onAction: (action: PlannerBoardActionIntent) => void;
};

export function DestinationDiscoveryCard({
  card,
  compact = false,
  disabled,
  onAction,
}: DestinationDiscoveryCardProps) {
  const [resolvedImage, setResolvedImage] = useState(() =>
    getDestinationSuggestionImagePreview(card),
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

  const isLeading = card.selection_status === "leading";
  const primaryTradeoff = card.tradeoffs?.find((tradeoff) => tradeoff.trim());
  const ctaLabel = isLeading ? "Lock destination" : "Explore this";
  const actionType = isLeading
    ? "confirm_destination_suggestion"
    : "select_destination_suggestion";
  const fallbackImage = getDestinationSuggestionImageFallback(card);

  return (
    <button
      type="button"
      disabled={disabled}
      onClick={() => {
        onAction({
          action_id: crypto.randomUUID(),
          type: actionType,
          destination_name: card.destination_name,
          country_or_region: card.country_or_region,
          suggestion_id: card.id,
        });
      }}
      className={cn(
        "group flex h-full cursor-pointer flex-col overflow-hidden rounded-[1.75rem] bg-[var(--planner-board-card)] text-left shadow-[0_1px_1px_rgba(0,0,0,0.04),0_10px_24px_rgba(0,0,0,0.05)] ring-1 transition-[transform,box-shadow,background-color] duration-200",
        isLeading ? "ring-[var(--planner-board-cta)]" : "ring-transparent",
        disabled
          ? "cursor-wait opacity-70"
          : "hover:-translate-y-0.5 hover:bg-[var(--planner-board-card-hover)] hover:shadow-[0_1px_1px_rgba(0,0,0,0.04),0_16px_30px_rgba(0,0,0,0.08)]",
      )}
    >
      <div
        className={cn(
          "relative overflow-hidden bg-[var(--planner-board-soft)]",
          compact ? "h-36" : "h-44",
        )}
      >
        <Image
          src={resolvedImage}
          alt={card.destination_name}
          fill
          onError={() => {
            if (resolvedImage !== fallbackImage) {
              setResolvedImage(fallbackImage);
            }
          }}
          className="object-cover transition-transform duration-700 group-hover:scale-[1.04]"
          sizes="(max-width: 1280px) 100vw, 50vw"
        />
      </div>
      <div className={cn("flex flex-1 flex-col", compact ? "p-5" : "p-6")}>
        <div className="mb-2 flex flex-wrap items-center gap-2">
          <span
            className={cn(
              "rounded px-2 py-0.5 text-[10px] font-bold uppercase tracking-[0.16em]",
              badgeClassName(card),
            )}
          >
            {badgeLabel(card)}
          </span>
          {isLeading ? (
            <span className="rounded bg-[var(--planner-board-cta)] px-2 py-0.5 text-[10px] font-bold uppercase tracking-[0.16em] text-white">
              Leading
            </span>
          ) : null}
          <span className="text-xs text-[var(--planner-board-muted-strong)]">
            {card.country_or_region}
          </span>
        </div>
        <h3 className="font-display text-[1.8rem] font-bold leading-none tracking-[-0.03em] text-[var(--planner-board-text)]">
          {card.destination_name}
        </h3>
        <p className="mt-3 text-sm leading-7 text-[var(--planner-board-muted)]">
          {card.short_reason}
        </p>
        {card.best_for ? (
          <p className="mt-4 rounded-lg bg-[var(--planner-board-soft)] px-3 py-2 text-xs font-semibold leading-5 text-[var(--planner-board-text)]">
            Best for {card.best_for}
          </p>
        ) : null}
        {primaryTradeoff ? (
          <p className="mt-3 text-xs leading-5 text-[var(--planner-board-muted)]">
            Worth knowing: {primaryTradeoff}
          </p>
        ) : null}
        {card.change_note ? (
          <p className="mt-3 text-xs leading-5 text-[var(--planner-board-muted-strong)]">
            {card.change_note}
          </p>
        ) : null}
        <span className="mt-6 inline-flex items-center gap-2 text-sm font-bold text-[var(--planner-board-cta)]">
          {ctaLabel}
          <ArrowRight className="h-4 w-4" />
        </span>
      </div>
    </button>
  );
}

function badgeLabel(card: DestinationSuggestionCard) {
  const label = card.fit_label?.trim() || card.practicality_label?.trim();
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
  return (
    BADGE_STYLES[normalized] ??
    "bg-[var(--planner-board-accent-soft)] text-[var(--planner-board-accent-text)]"
  );
}
