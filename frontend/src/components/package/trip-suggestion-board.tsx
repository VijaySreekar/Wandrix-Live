"use client";

import { useEffect, useState } from "react";
import Image from "next/image";
import {
  ArrowRight,
  CalendarRange,
  ChevronDown,
  ChevronUp,
  MapPin,
} from "lucide-react";

import { getLiveDestinationImage } from "@/components/package/trip-board-cards";
import { resolveDestinationSuggestionImage } from "@/lib/destination-images";
import { cn } from "@/lib/utils";
import type { PlannerBoardActionIntent } from "@/types/planner-board";
import type {
  AdvancedDateOptionCard,
  AdvancedAnchorChoiceCard,
  AdvancedStayHotelOptionCard,
  AdvancedStayOptionCard,
  DestinationSuggestionCard,
  PlanningModeChoiceCard,
  PlannerHotelStyleTag,
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

  if (board.mode === "advanced_date_resolution") {
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
          <AdvancedDateResolutionPanel
            board={board}
            disabled={disabled}
            onAction={onAction}
          />
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

  if (
    board.mode === "advanced_stay_choice" ||
    board.mode === "advanced_stay_selected" ||
    board.mode === "advanced_stay_review"
  ) {
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
          {(board.mode === "advanced_stay_selected" ||
            board.mode === "advanced_stay_review") &&
          board.selected_stay_option_id ? (
            <AdvancedStayStatusPanel board={board} />
          ) : null}

          <div className="grid gap-4">
            {(board.stay_cards ?? []).map((card) => (
              <AdvancedStayOptionCardView
                key={card.id}
                card={card}
                board={board}
                disabled={disabled}
                onAction={onAction}
              />
            ))}
          </div>
        </div>
      </section>
    );
  }

  if (
    board.mode === "advanced_stay_hotel_choice" ||
    board.mode === "advanced_stay_hotel_selected" ||
    board.mode === "advanced_stay_hotel_review"
  ) {
    const hotelFilters = board.hotel_filters ?? {
      max_nightly_rate: null,
      area_filter: null,
      style_filter: null,
    };
    const hotelSortOrder = board.hotel_sort_order ?? "best_fit";
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
          <AdvancedStayHotelWorkspace
            key={`${hotelFilters.max_nightly_rate ?? "none"}-${hotelFilters.area_filter ?? "all"}-${hotelFilters.style_filter ?? "all"}-${hotelSortOrder}-${board.hotel_page ?? 1}`}
            board={board}
            disabled={disabled}
            onAction={onAction}
          />
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
  const isCompleted = card.status === "completed";
  return (
    <article
      className={cn(
        "rounded-xl border px-6 py-6 shadow-[0_1px_1px_rgba(0,0,0,0.04),0_8px_18px_rgba(0,0,0,0.04)]",
        isCompleted
          ? "border-[var(--planner-board-border)] bg-[var(--planner-board-soft)]"
          : "border-[var(--planner-board-border)] bg-[var(--planner-board-card)]",
      )}
    >
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h3
            className={cn(
              "font-display text-xl font-bold tracking-[-0.02em]",
              isCompleted
                ? "text-[var(--planner-board-muted-strong)]"
                : "text-[var(--planner-board-text)]",
            )}
          >
            {card.title}
          </h3>
          <p
            className={cn(
              "mt-2 max-w-xl text-sm leading-7",
              isCompleted
                ? "text-[var(--planner-board-muted-strong)]"
                : "text-[var(--planner-board-muted)]",
            )}
          >
            {card.description}
          </p>
        </div>
        {card.badge ? (
          <span
            className={cn(
              "rounded-md border px-2.5 py-1 text-[11px] font-semibold uppercase tracking-[0.14em]",
              isCompleted
                ? "border-[var(--planner-board-border)] bg-[var(--planner-board-card)] text-[var(--planner-board-muted-strong)]"
                : "border-[color:color-mix(in_srgb,var(--accent)_24%,transparent)] bg-[color:color-mix(in_srgb,var(--accent)_10%,transparent)] text-[color:var(--accent)]",
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
                isCompleted
                  ? "bg-[var(--planner-board-muted-strong)]"
                  : card.recommended
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
          disabled={disabled || isCompleted}
          onClick={() =>
            onAction({
              action_id: crypto.randomUUID(),
              type: "select_advanced_anchor",
              advanced_anchor: card.id,
            })
          }
          className={cn(
            "inline-flex items-center rounded-lg border px-4 py-2.5 text-sm font-semibold transition-colors",
            disabled || isCompleted
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

function AdvancedStayHotelWorkspace({
  board,
  disabled,
  onAction,
}: {
  board: TripSuggestionBoardState;
  disabled: boolean;
  onAction: (action: PlannerBoardActionIntent) => void;
}) {
  const hotelCards = (board.hotel_cards ?? []).slice(0, 4);
  const workspaceBlocked = board.hotel_results_status === "blocked";
  const hasResults = hotelCards.length > 0;

  return (
    <section className="space-y-3">
      <p className="max-w-3xl text-sm leading-6 text-[var(--planner-board-muted)]">
        {workspaceBlocked
          ? board.hotel_results_summary ||
            "Hotel fit can still be discussed here, but exact hotel comparison needs fixed dates first."
          : "Four hotel recommendations, shaped around the stay direction you chose. Open any card for more detail, and tell me in chat what feels too expensive, too central, or just not right if you want me to recut the shortlist."}
      </p>

      {workspaceBlocked ? (
        <WorkspaceNotice
          title="Exact hotel comparison is still gated"
          description={
            board.hotel_results_summary ||
            "Hotel fit can still be discussed here, but exact hotel comparison needs fixed dates first."
          }
        />
      ) : null}

      {hasResults ? (
        <div className="space-y-3">
          {hotelCards.map((card) => (
            <AdvancedStayHotelCardView
              key={card.id}
              card={card}
              board={board}
              disabled={disabled || workspaceBlocked}
              onAction={onAction}
            />
          ))}
        </div>
      ) : workspaceBlocked ? null : (
        <WorkspaceNotice
          title="No hotel recommendations are ready yet"
          description="I need a little more stay signal before I can shape a stronger shortlist inside this base."
        />
      )}
    </section>
  );
}

function WorkspaceNotice({
  title,
  description,
}: {
  title: string;
  description: string;
}) {
  return (
    <article className="rounded-lg border border-dashed border-[var(--planner-board-border)] bg-[var(--planner-board-card)] px-4 py-4">
      <h3 className="text-sm font-semibold text-[var(--planner-board-text)]">
        {title}
      </h3>
      <p className="mt-1.5 text-sm leading-6 text-[var(--planner-board-muted)]">
        {description}
      </p>
    </article>
  );
}

function AdvancedStayStatusPanel({
  board,
  compact = false,
}: {
  board: TripSuggestionBoardState;
  compact?: boolean;
}) {
  const selectedCard = (board.stay_cards ?? []).find(
    (card) => card.id === board.selected_stay_option_id,
  );

  if (!selectedCard) {
    return null;
  }

  const statusLabel =
    board.mode === "advanced_stay_review"
      ? "Stay needs review"
      : board.stay_selection_status === "selected"
        ? "Stay direction"
        : "Stay";

  return (
    <article
      className={cn(
        "rounded-lg border border-[var(--planner-board-border)] bg-[var(--planner-board-card)] shadow-[0_1px_1px_rgba(0,0,0,0.03),0_4px_12px_rgba(0,0,0,0.04)]",
        compact ? "px-4 py-3" : "mb-4 px-5 py-4",
      )}
    >
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0">
          <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-[var(--planner-board-muted-strong)]">
            {statusLabel}
          </p>
          <h3
            className={cn(
              "mt-1 font-display font-bold tracking-[-0.02em] text-[var(--planner-board-text)]",
              compact ? "text-base" : "text-lg",
            )}
          >
            {selectedCard.title}
          </h3>
          <p className="mt-2 max-w-3xl text-sm leading-6 text-[var(--planner-board-muted)]">
            {board.stay_selection_rationale || selectedCard.summary}
          </p>
        </div>
        <span
          className={cn(
            "rounded-md border px-2 py-0.5 text-[10px] font-semibold uppercase tracking-[0.14em]",
            board.mode === "advanced_stay_review"
              ? "border-[color:color-mix(in_srgb,#b45309_28%,transparent)] bg-[color:color-mix(in_srgb,#f59e0b_12%,transparent)] text-[#92400e]"
              : "border-[color:color-mix(in_srgb,var(--accent)_24%,transparent)] bg-[color:color-mix(in_srgb,var(--accent)_10%,transparent)] text-[color:var(--accent)]",
          )}
        >
          {board.mode === "advanced_stay_review" ? "Review" : "Active"}
        </span>
      </div>

      {(board.stay_selection_assumptions?.length ||
        board.stay_compatibility_notes?.length) ? (
        <div
          className={cn(
            "grid gap-3",
            compact ? "mt-2" : "mt-3 lg:grid-cols-2",
          )}
        >
          {board.stay_selection_assumptions?.length ? (
            <div>
              <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-[var(--planner-board-muted-strong)]">
                Built Around
              </p>
              <ul className="mt-2 flex flex-wrap gap-2">
                {board.stay_selection_assumptions
                  .slice(0, compact ? 2 : 3)
                  .map((item) => (
                  <li
                    key={item}
                    className="rounded-md border border-[var(--planner-board-border)] bg-[var(--planner-board-soft)] px-2.5 py-1 text-xs text-[var(--planner-board-muted)]"
                  >
                    {item}
                  </li>
                ))}
              </ul>
            </div>
          ) : null}

          {board.stay_compatibility_notes?.length ? (
            <div>
              <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-[var(--planner-board-muted-strong)]">
                Compatibility Notes
              </p>
              <ul className="mt-2 space-y-2">
                {board.stay_compatibility_notes.slice(0, 1).map((item) => (
                  <li
                    key={item}
                    className="rounded-lg border border-[color:color-mix(in_srgb,#b45309_18%,transparent)] bg-[color:color-mix(in_srgb,#f59e0b_8%,transparent)] px-3 py-2 text-xs leading-5 text-[var(--planner-board-muted)]"
                  >
                    {item}
                  </li>
                ))}
              </ul>
            </div>
          ) : null}
        </div>
      ) : null}
    </article>
  );
}

function AdvancedStayOptionCardView({
  card,
  board,
  disabled,
  onAction,
}: {
  card: AdvancedStayOptionCard;
  board: TripSuggestionBoardState;
  disabled: boolean;
  onAction: (action: PlannerBoardActionIntent) => void;
}) {
  const isSelected = board.selected_stay_option_id === card.id;
  const isReviewMode = board.mode === "advanced_stay_review" && isSelected;

  return (
    <article
      className={cn(
        "rounded-xl border bg-[var(--planner-board-card)] px-6 py-6 shadow-[0_1px_1px_rgba(0,0,0,0.04),0_8px_18px_rgba(0,0,0,0.04)]",
        isSelected
          ? "border-[color:color-mix(in_srgb,var(--accent)_30%,transparent)]"
          : "border-[var(--planner-board-border)]",
      )}
    >
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <div className="flex flex-wrap items-center gap-2">
            <h3 className="font-display text-xl font-bold tracking-[-0.02em] text-[var(--planner-board-text)]">
              {card.title}
            </h3>
            {card.badge ? (
              <span className="rounded-md border border-[color:color-mix(in_srgb,var(--accent)_24%,transparent)] bg-[color:color-mix(in_srgb,var(--accent)_10%,transparent)] px-2.5 py-1 text-[11px] font-semibold uppercase tracking-[0.14em] text-[color:var(--accent)]">
                {card.badge}
              </span>
            ) : null}
            {isSelected ? (
              <span
                className={cn(
                  "rounded-md border px-2.5 py-1 text-[11px] font-semibold uppercase tracking-[0.14em]",
                  isReviewMode
                    ? "border-[color:color-mix(in_srgb,#b45309_28%,transparent)] bg-[color:color-mix(in_srgb,#f59e0b_12%,transparent)] text-[#92400e]"
                    : "border-[color:color-mix(in_srgb,var(--accent)_24%,transparent)] bg-[color:color-mix(in_srgb,var(--accent)_10%,transparent)] text-[color:var(--accent)]",
                )}
              >
                {isReviewMode ? "Needs review" : "Selected"}
              </span>
            ) : null}
          </div>
          <p className="mt-2 max-w-xl text-sm leading-7 text-[var(--planner-board-muted)]">
            {card.summary}
          </p>
        </div>
        <div className="text-right">
          <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-[var(--planner-board-muted-strong)]">
            {card.strategy_type === "split_stay" ? "Strategy" : "Area direction"}
          </p>
          <p className="mt-1 text-sm font-medium text-[var(--planner-board-text)]">
            {card.area_label || card.areas.join(", ") || "Flexible area base"}
          </p>
        </div>
      </div>

      <div className="mt-5 grid gap-4 lg:grid-cols-2">
        <div>
          <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-[var(--planner-board-muted-strong)]">
            Best For
          </p>
          <ul className="mt-3 space-y-2">
            {card.best_for.map((bullet) => (
              <li
                key={bullet}
                className="flex items-start gap-3 text-sm leading-7 text-[var(--planner-board-muted)]"
              >
                <span className="mt-2 block h-1.5 w-1.5 rounded-full bg-[color:var(--accent)]" />
                <span>{bullet}</span>
              </li>
            ))}
          </ul>
        </div>

        <div>
          <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-[var(--planner-board-muted-strong)]">
            Tradeoffs
          </p>
          <ul className="mt-3 space-y-2">
            {card.tradeoffs.map((bullet) => (
              <li
                key={bullet}
                className="flex items-start gap-3 text-sm leading-7 text-[var(--planner-board-muted)]"
              >
                <span className="mt-2 block h-1.5 w-1.5 rounded-full bg-[var(--planner-board-muted-strong)]" />
                <span>{bullet}</span>
              </li>
            ))}
          </ul>
        </div>
      </div>

      <div className="mt-6">
        <button
          type="button"
          disabled={disabled}
          onClick={() =>
            onAction({
              action_id: crypto.randomUUID(),
              type: "select_stay_option",
              stay_option_id: card.id,
              stay_segment_id: card.segment_id,
            })
          }
          className={cn(
            "inline-flex items-center rounded-lg border px-4 py-2.5 text-sm font-semibold transition-colors",
            disabled
              ? "cursor-not-allowed border-[var(--planner-board-border)] bg-[var(--planner-board-soft)] text-[var(--planner-board-muted-strong)]"
              : isSelected
                ? "border-[color:var(--accent)] bg-[color:color-mix(in_srgb,var(--accent)_10%,white)] text-[color:var(--accent)] hover:bg-[color:color-mix(in_srgb,var(--accent)_14%,white)]"
                : "border-[color:var(--accent)] bg-[color:var(--accent)] text-[color:var(--accent-foreground)] hover:bg-[color:color-mix(in_srgb,var(--accent)_92%,black)]",
          )}
        >
          {isSelected ? "Selected stay direction" : card.cta_label || "Choose this base"}
        </button>
      </div>
    </article>
  );
}

function AdvancedStayHotelCardView({
  card,
  board,
  disabled,
  onAction,
}: {
  card: AdvancedStayHotelOptionCard;
  board: TripSuggestionBoardState;
  disabled: boolean;
  onAction: (action: PlannerBoardActionIntent) => void;
}) {
  const isSelected = board.selected_hotel_id === card.id;
  const isReviewMode = board.mode === "advanced_stay_hotel_review" && isSelected;
  const nightlyRate = formatNightlyRate(card);
  const stayWindow = formatBoardDateRange(card.check_in, card.check_out);
  const workspaceBlocked = board.hotel_results_status === "blocked";
  const areaLabel = normalizeAreaLabel(card.area);
  const [expanded, setExpanded] = useState(isSelected || card.recommended);
  const isExpanded = expanded || isSelected;

  return (
    <article
      className={cn(
        "overflow-hidden rounded-xl border border-[var(--planner-board-border)] bg-[var(--planner-board-card)]",
        isSelected
          ? "bg-[color:color-mix(in_srgb,var(--planner-board-soft)_38%,white)]"
          : "",
      )}
    >
      <div className="grid gap-4 px-5 py-4 lg:grid-cols-[220px_minmax(0,1fr)_132px] lg:items-start">
        <HotelVisual
          imageUrl={card.image_url}
          hotelName={card.hotel_name}
          area={areaLabel}
          badges={[
            ...(card.recommended ? ["Best fit"] : []),
            ...(isSelected ? [isReviewMode ? "Needs review" : "Selected"] : []),
          ]}
        />

        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-2.5">
            <h3 className="text-base font-semibold tracking-tight text-[var(--planner-board-text)]">
              {card.hotel_name}
            </h3>
            {card.recommended ? (
              <span className="rounded-md bg-[var(--planner-board-soft)] px-2 py-1 text-[11px] font-medium text-[var(--planner-board-muted-strong)]">
                Best fit
              </span>
            ) : null}
            {isSelected ? (
              <span className="rounded-md bg-[color:color-mix(in_srgb,var(--accent)_10%,white)] px-2 py-1 text-[11px] font-medium text-[color:var(--accent)]">
                {isReviewMode ? "Needs review" : "Selected"}
              </span>
            ) : null}
          </div>
          <div className="mt-1.5 flex flex-wrap items-center gap-x-4 gap-y-2 text-sm text-[var(--planner-board-muted)]">
            <span className="inline-flex items-center gap-2">
              <MapPin className="h-4 w-4 text-[var(--accent)]" />
              {areaLabel}
            </span>
            <span className="inline-flex items-center gap-2">
              <CalendarRange className="h-4 w-4 text-[var(--accent)]" />
              {stayWindow}
            </span>
          </div>
          <p className="mt-3 max-w-3xl text-sm leading-6 text-[var(--planner-board-text)]">
            {card.why_it_fits}
          </p>

          <div className="mt-3 flex flex-wrap gap-2">
            {card.style_tags.slice(0, 2).map((tag) => (
              <span
                key={tag}
                className="rounded-md border border-[var(--planner-board-border)] bg-[var(--planner-board-soft)] px-2.5 py-1 text-xs text-[var(--planner-board-muted)]"
              >
                {formatHotelStyleLabel(tag)}
              </span>
            ))}
            {card.tradeoffs.slice(0, 1).map((item) => (
              <span
                key={item}
                className="rounded-md border border-[var(--planner-board-border)] bg-[var(--planner-board-soft)] px-2.5 py-1 text-xs text-[var(--planner-board-muted)]"
              >
                {item}
              </span>
            ))}
            {card.outside_active_filters ? (
              <span className="rounded-md border border-[color:color-mix(in_srgb,#b45309_18%,transparent)] bg-[color:color-mix(in_srgb,#f59e0b_8%,transparent)] px-2.5 py-1 text-xs text-[#92400e]">
                Outside current filters
              </span>
            ) : null}
          </div>

          {isExpanded ? (
            <div className="mt-4 grid gap-3 border-t border-[var(--planner-board-border)] pt-4 text-sm text-[var(--planner-board-muted)] lg:grid-cols-[minmax(0,1fr)_minmax(0,0.9fr)]">
              <div>
                <p className="text-[11px] font-semibold uppercase tracking-[0.14em] text-[var(--planner-board-muted-strong)]">
                  Why it works
                </p>
                <p className="mt-2 leading-6">{card.summary}</p>
              </div>
              <div>
                <p className="text-[11px] font-semibold uppercase tracking-[0.14em] text-[var(--planner-board-muted-strong)]">
                  Tradeoffs
                </p>
                <ul className="mt-2 space-y-2">
                  {card.tradeoffs.slice(0, 2).map((item) => (
                    <li key={item} className="leading-6">
                      {item}
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          ) : null}
        </div>

        <div className="flex flex-col items-start gap-4 lg:items-end">
          <PricePanel
            title={nightlyRate.title}
            primary={nightlyRate.primary}
            secondary={nightlyRate.secondary}
          />
          <button
            type="button"
            disabled={disabled || workspaceBlocked}
            onClick={() =>
              onAction({
                action_id: crypto.randomUUID(),
                type: "select_stay_hotel",
                stay_hotel_id: card.id,
                stay_hotel_name: card.hotel_name,
              })
            }
            className={cn(
              "inline-flex items-center rounded-md border px-3.5 py-2 text-sm font-semibold transition-colors",
              disabled || workspaceBlocked
                ? "cursor-not-allowed border-[var(--planner-board-border)] bg-[var(--planner-board-soft)] text-[var(--planner-board-muted-strong)]"
                : isSelected
                  ? "border-[color:var(--accent)] bg-[color:color-mix(in_srgb,var(--accent)_10%,white)] text-[color:var(--accent)] hover:bg-[color:color-mix(in_srgb,var(--accent)_14%,white)]"
                  : "border-[color:var(--accent)] bg-[color:var(--accent)] text-[color:var(--accent-foreground)] hover:bg-[color:color-mix(in_srgb,var(--accent)_92%,black)]",
            )}
          >
            {isSelected ? "Selected" : card.cta_label || "Choose this hotel"}
          </button>
          <button
            type="button"
            onClick={() => setExpanded((current) => !current)}
            className="inline-flex items-center gap-1.5 text-xs font-medium text-[var(--planner-board-muted-strong)] transition-colors hover:text-[var(--planner-board-text)]"
          >
            {isExpanded ? "Less detail" : "More detail"}
            {isExpanded ? <ChevronUp className="h-3.5 w-3.5" /> : <ChevronDown className="h-3.5 w-3.5" />}
          </button>
        </div>
      </div>
    </article>
  );
}

function HotelVisual({
  imageUrl,
  hotelName,
  area,
  badges,
  variant = "default",
}: {
  imageUrl?: string | null;
  hotelName: string;
  area?: string | null;
  badges: string[];
  variant?: "default" | "featured";
}) {
  const heightClass =
    variant === "featured" ? "min-h-[220px]" : "min-h-[168px]";

  if (imageUrl) {
    return (
      <div className={cn("relative overflow-hidden rounded-lg bg-[var(--planner-board-soft)]", heightClass)}>
        <Image
          src={imageUrl}
          alt={hotelName}
          fill
          className="object-cover"
          sizes={variant === "featured" ? "(max-width: 1024px) 100vw, 360px" : "(max-width: 1024px) 100vw, 320px"}
        />
        <div className="absolute inset-0 bg-[linear-gradient(180deg,rgba(17,24,39,0.02),rgba(17,24,39,0.2))]" />
        <div className="absolute left-3 top-3 flex flex-wrap gap-2">
          {badges.map((badge) => (
            <span
              key={badge}
              className="rounded-md bg-[rgba(255,255,255,0.84)] px-2 py-0.5 text-[10px] font-medium text-[var(--planner-board-text)] backdrop-blur-sm"
            >
              {badge}
            </span>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div
      className={cn(
        "relative overflow-hidden rounded-lg border border-[var(--planner-board-border)] bg-[var(--planner-board-soft)]",
        heightClass,
      )}
    >
      <div className="absolute left-3 top-3 flex flex-wrap gap-2">
        {badges.map((badge) => (
          <span
            key={badge}
            className="rounded-md bg-white px-2 py-0.5 text-[10px] font-medium text-[var(--planner-board-text)]"
          >
            {badge}
          </span>
        ))}
      </div>
      <div className="flex h-full flex-col justify-end px-4 py-4">
        <p className="text-[11px] font-medium text-[var(--planner-board-muted-strong)]">
          Image unavailable
        </p>
        <p className="mt-2 text-xl font-semibold tracking-tight text-[var(--planner-board-text)]">
          {hotelName}
        </p>
        <p className="mt-2 text-sm leading-6 text-[var(--planner-board-muted)]">
          {area || "Area still being refined"}
        </p>
      </div>
    </div>
  );
}

function PricePanel({
  title,
  primary,
  secondary,
}: {
  title: string;
  primary: string;
  secondary: string;
}) {
  return (
    <div className="min-w-[132px] text-left lg:text-right">
      <p className="text-[11px] font-medium text-[var(--planner-board-muted-strong)]">
        {title}
      </p>
      <p className="mt-1 text-base font-semibold tracking-tight text-[var(--planner-board-text)]">
        {primary}
      </p>
      <p className="mt-1 text-xs leading-5 text-[var(--planner-board-muted)]">
        {secondary}
      </p>
    </div>
  );
}

function AdvancedDateResolutionPanel({
  board,
  disabled,
  onAction,
}: {
  board: TripSuggestionBoardState;
  disabled: boolean;
  onAction: (action: PlannerBoardActionIntent) => void;
}) {
  const selectedOption =
    (board.date_option_cards ?? []).find(
      (option) => option.id === board.selected_date_option_id,
    ) ?? null;

  return (
    <div className="space-y-5">
      <div className="rounded-2xl border border-[var(--planner-board-border)] bg-[var(--planner-board-card)] p-5">
        <div className="grid gap-3 md:grid-cols-2">
          <ContextStat
            label="Destination"
            value={board.have_details.find((item) => item.id === "destination")?.value || "Still shaping"}
          />
          <ContextStat
            label="Rough timing"
            value={board.source_timing_text || "Still flexible"}
          />
          <ContextStat
            label="Trip length"
            value={board.source_trip_length_text || "Still flexible"}
          />
          <ContextStat
            label="Route"
            value={
              board.have_details.find((item) => item.id === "route")?.value ||
              "Departure can still stay flexible"
            }
          />
        </div>
      </div>

      <div className="grid gap-3">
        {(board.date_option_cards ?? []).map((card) => (
          <AdvancedDateOptionCardView
            key={card.id}
            card={card}
            board={board}
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
            type: "pick_dates_for_me",
          })
        }
        className={cn(
          "flex w-full items-center justify-between rounded-2xl border border-[var(--planner-board-border)] bg-[var(--planner-board-card)] px-5 py-4 text-left transition-colors duration-150",
          disabled
            ? "cursor-wait opacity-70"
            : "hover:bg-[var(--planner-board-card-hover)]",
        )}
      >
        <div>
          <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-[var(--planner-board-muted-strong)]">
            Wandrix can choose
          </p>
          <p className="mt-1 text-sm font-semibold text-[var(--planner-board-text)]">
            Pick the strongest date option for me
          </p>
          <p className="mt-1 text-sm text-[var(--planner-board-muted)]">
            I’ll choose the recommended window, explain why it wins, and still wait for your go-ahead before proceeding.
          </p>
        </div>
        <ArrowRight className="h-4 w-4 text-[var(--planner-board-cta)]" />
      </button>

      {selectedOption ? (
        <div className="rounded-2xl border border-[var(--planner-board-border)] bg-[var(--planner-board-card)] p-5">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-[var(--planner-board-muted-strong)]">
                Working trip window
              </p>
              <h3 className="mt-1 text-base font-semibold text-[var(--planner-board-text)]">
                {selectedOption.title}
              </h3>
              <p className="mt-1 text-sm text-[var(--planner-board-muted)]">
                {selectedOption.reason}
              </p>
            </div>
            <button
              type="button"
              disabled={disabled}
              onClick={() =>
                onAction({
                  action_id: crypto.randomUUID(),
                  type: "confirm_working_dates",
                  date_option_id: selectedOption.id,
                  start_date: selectedOption.start_date,
                  end_date: selectedOption.end_date,
                  trip_length: board.source_trip_length_text || null,
                })
              }
              className={cn(
                "inline-flex items-center gap-2 rounded-lg bg-[var(--planner-board-cta)] px-4 py-2 text-sm font-semibold text-white transition-opacity duration-150",
                disabled ? "cursor-wait opacity-70" : "hover:opacity-90",
              )}
            >
              Proceed with this trip window
              <ArrowRight className="h-4 w-4" />
            </button>
          </div>
        </div>
      ) : null}
    </div>
  );
}

function AdvancedDateOptionCardView({
  card,
  board,
  disabled,
  onAction,
}: {
  card: AdvancedDateOptionCard;
  board: TripSuggestionBoardState;
  disabled: boolean;
  onAction: (action: PlannerBoardActionIntent) => void;
}) {
  const isSelected = board.selected_date_option_id === card.id;

  return (
    <button
      type="button"
      disabled={disabled}
      onClick={() =>
        onAction({
          action_id: crypto.randomUUID(),
          type: "select_date_option",
          date_option_id: card.id,
        })
      }
      className={cn(
        "w-full rounded-2xl border px-5 py-4 text-left transition-colors duration-150",
        isSelected
          ? "border-[var(--planner-board-cta)] bg-[var(--planner-board-card)]"
          : "border-[var(--planner-board-border)] bg-[var(--planner-board-card)] hover:bg-[var(--planner-board-card-hover)]",
        disabled ? "cursor-wait opacity-70" : "cursor-pointer",
      )}
    >
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <div className="flex items-center gap-2">
            <h3 className="text-base font-semibold text-[var(--planner-board-text)]">
              {card.title}
            </h3>
            {card.recommended ? (
              <span className="rounded-md bg-[var(--planner-board-soft)] px-2 py-1 text-[11px] font-semibold text-[var(--planner-board-accent-text)]">
                Recommended
              </span>
            ) : null}
            {isSelected ? (
              <span className="rounded-md bg-[var(--planner-board-accent-soft)] px-2 py-1 text-[11px] font-semibold text-[var(--planner-board-accent-text)]">
                Selected
              </span>
            ) : null}
          </div>
          <p className="mt-2 text-sm text-[var(--planner-board-muted)]">
            {card.reason}
          </p>
        </div>
        <div className="min-w-[148px] rounded-xl border border-[var(--planner-board-border)] bg-[var(--planner-board-soft)] px-3 py-3">
          <div className="flex items-center gap-2 text-[var(--planner-board-text)]">
            <CalendarRange className="h-4 w-4" />
            <span className="text-sm font-semibold">
              {formatBoardDateShort(card.start_date)} to{" "}
              {formatBoardDateShort(card.end_date)}
            </span>
          </div>
          <p className="mt-1 text-xs text-[var(--planner-board-muted)]">
            {card.nights} {card.nights === 1 ? "night" : "nights"}
          </p>
        </div>
      </div>
    </button>
  );
}

function ContextStat({
  label,
  value,
}: {
  label: string;
  value: string;
}) {
  return (
    <div>
      <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-[var(--planner-board-muted-strong)]">
        {label}
      </p>
      <p className="mt-1 text-sm font-medium text-[var(--planner-board-text)]">
        {value}
      </p>
    </div>
  );
}

function formatNightlyRate(card: AdvancedStayHotelOptionCard) {
  if (typeof card.nightly_rate_amount === "number") {
    const currency = (card.nightly_rate_currency || "GBP").toUpperCase();
    const formatter = new Intl.NumberFormat("en-GB", {
      style: "currency",
      currency,
      maximumFractionDigits: 0,
    });

    const primary = `${formatter.format(card.nightly_rate_amount)} / night`;
    const noteParts = [
      card.rate_provider_name ? `via ${card.rate_provider_name}` : null,
      typeof card.nightly_tax_amount === "number"
        ? `taxes about ${formatter.format(card.nightly_tax_amount)}`
        : null,
    ].filter(Boolean);

    return {
      title: "Nightly rate",
      primary,
      secondary:
        card.rate_note ||
        noteParts.join(" | ") ||
        "Live rate pulled for the exact stay dates.",
    };
  }

  if (card.check_in && card.check_out) {
    return {
      title: "Nightly rate",
      primary: "Live rate unavailable",
      secondary:
        card.rate_note ||
        "These dates are fixed, but this provider did not return a usable nightly rate yet.",
    };
  }

  return {
    title: "Nightly rate",
    primary: "Dates needed",
    secondary:
      card.rate_note ||
      "Lock the stay dates to compare exact nightly hotel prices.",
  };
}

function formatBoardDateRange(
  checkIn: string | null | undefined,
  checkOut: string | null | undefined,
) {
  if (!checkIn && !checkOut) {
    return "Stay window still flexible";
  }

  return `${formatBoardDateShort(checkIn)} to ${formatBoardDateShort(checkOut)}`;
}

function formatBoardDateShort(value: string | null | undefined) {
  if (!value) {
    return "TBD";
  }

  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) {
    return value;
  }

  return parsed.toLocaleDateString("en-GB", {
    day: "numeric",
    month: "short",
  });
}

function formatHotelStyleLabel(style: PlannerHotelStyleTag) {
  return (
    {
      calm: "Calm",
      central: "Central",
      design: "Design-led",
      luxury: "Luxury",
      food_access: "Food access",
      practical: "Practical",
      traditional: "Traditional",
      nightlife: "Nightlife",
      walkable: "Walkable",
      value: "Value",
    }[style] ?? style.replace("_", " ").replace(/\b\w/g, (character) => character.toUpperCase())
  );
}

function normalizeAreaLabel(value: string | null | undefined) {
  if (!value) {
    return "This part of Kyoto";
  }

  const cleaned = value
    .replace(/-ku\b/gi, "-ku")
    .replace(/,\s*Japan\b/gi, "")
    .replace(/\bJapan\b/gi, "")
    .replace(/\bKyoto Prefecture\b/gi, "Kyoto")
    .replace(/\s+,/g, ",")
    .replace(/,\s*,/g, ",")
    .replace(/\s{2,}/g, " ")
    .replace(/,\s*$/g, "")
    .replace(/^,\s*/g, "")
    .trim();

  return cleaned || "This part of Kyoto";
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
      <div className="relative h-44 overflow-hidden bg-[var(--planner-board-soft)]">
        <Image
          src={resolvedImage}
          alt={card.destination_name}
          fill
          className="object-cover transition-transform duration-700 group-hover:scale-[1.04]"
          sizes="(max-width: 1280px) 100vw, 50vw"
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
