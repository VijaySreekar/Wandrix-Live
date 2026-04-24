"use client";

import { useEffect, useState } from "react";
import Image from "next/image";
import {
  ArrowRight,
  CalendarRange,
  ChevronDown,
  ChevronUp,
  Clock,
  ExternalLink,
  MapPin,
  Plane,
} from "lucide-react";

import { getLiveDestinationImage } from "@/components/package/trip-board-cards";
import { resolveDestinationSuggestionImage } from "@/lib/destination-images";
import { cn } from "@/lib/utils";
import type { PlannerBoardActionIntent } from "@/types/planner-board";
import type {
  AdvancedActivityCandidateCard,
  AdvancedDateOptionCard,
  AdvancedAnchorChoiceCard,
  AdvancedReviewDecisionSignal,
  AdvancedReviewSectionCard,
  AdvancedFlightOptionCard,
  AdvancedStayHotelOptionCard,
  AdvancedStayOptionCard,
  DestinationSuggestionCard,
  PlanningModeChoiceCard,
  PlannerActivityDaypart,
  PlannerAdvancedAnchor,
  PlannerConflictRecord,
  PlannerHotelStyleTag,
  PlannerTripPace,
  PlannerTripStyleTradeoffAxis,
  PlannerTripDirectionAccent,
  PlannerTripDirectionPrimary,
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
                "The first deeper planning focus is now selected.",
                "That choice now becomes the main path between flights, stay, trip style, or experiences.",
                "The current brief still stays editable in chat if you want to adjust it before the deeper planning begins.",
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

  if (board.mode === "advanced_flights_workspace") {
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
          <AdvancedFlightsWorkspace
            board={board}
            disabled={disabled}
            onAction={onAction}
          />
        </div>
      </section>
    );
  }

  if (board.mode === "advanced_trip_style_direction") {
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
          <AdvancedTripStyleWorkspace
            board={board}
            disabled={disabled}
            onAction={onAction}
          />
        </div>
      </section>
    );
  }

  if (board.mode === "advanced_trip_style_pace") {
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
          <AdvancedTripStylePaceWorkspace
            board={board}
            disabled={disabled}
            onAction={onAction}
          />
        </div>
      </section>
    );
  }

  if (board.mode === "advanced_trip_style_tradeoffs") {
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
          <AdvancedTripStyleTradeoffsWorkspace
            board={board}
            disabled={disabled}
            onAction={onAction}
          />
        </div>
      </section>
    );
  }

  if (board.mode === "advanced_activities_workspace") {
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
          <AdvancedActivitiesWorkspace
            board={board}
            disabled={disabled}
            onAction={onAction}
          />
        </div>
      </section>
    );
  }

  if (board.mode === "advanced_review_workspace") {
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
          <AdvancedReviewWorkspace
            board={board}
            disabled={disabled}
            onAction={onAction}
          />
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
            <AdvancedStayStatusPanel
              board={board}
              disabled={disabled}
              onAction={onAction}
            />
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

function AdvancedFlightsWorkspace({
  board,
  disabled,
  onAction,
}: {
  board: TripSuggestionBoardState;
  disabled: boolean;
  onAction: (action: PlannerBoardActionIntent) => void;
}) {
  const strategies = board.flight_strategy_cards ?? [];
  const outboundOptions = board.outbound_flight_options ?? [];
  const returnOptions = board.return_flight_options ?? [];
  const selectedStrategy = board.selected_flight_strategy ?? null;
  const selectedOutboundId = board.selected_outbound_flight_id ?? null;
  const selectedReturnId = board.selected_return_flight_id ?? null;
  const blocked = board.flight_results_status === "blocked";
  const canConfirm =
    !blocked &&
    (selectedStrategy === "keep_flexible" ||
      Boolean(selectedOutboundId && selectedReturnId));

  return (
    <div className="space-y-6">
      <div className="rounded-xl border border-[var(--planner-board-border)] bg-[var(--planner-board-card)] px-5 py-4">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div className="min-w-0 flex-1">
            <p className="text-xs font-semibold uppercase tracking-[0.14em] text-[var(--planner-board-muted-strong)]">
              Route readiness
            </p>
            {board.flight_workspace_summary ? (
              <p className="mt-2 text-sm leading-6 text-[var(--planner-board-muted)]">
                {board.flight_workspace_summary}
              </p>
            ) : null}
            {board.flight_selection_summary ? (
              <p className="mt-2 text-sm font-medium leading-6 text-[var(--planner-board-text)]">
                {board.flight_selection_summary}
              </p>
            ) : null}
          </div>
          <span className="rounded-md bg-[var(--planner-board-soft)] px-3 py-2 text-[11px] font-semibold uppercase tracking-[0.12em] text-[var(--planner-board-accent-text)]">
            {formatFlightResultsStatus(board.flight_results_status)}
          </span>
        </div>
        {blocked && board.flight_missing_requirements?.length ? (
          <div className="mt-4 flex flex-wrap gap-2">
            {board.flight_missing_requirements.map((item) => (
              <span
                key={item}
                className="rounded-md border border-[var(--planner-board-border)] px-2.5 py-1 text-[11px] font-medium text-[var(--planner-board-muted-strong)]"
              >
                Needs {item}
              </span>
            ))}
          </div>
        ) : null}
        {board.have_details.length || board.need_details.length ? (
          <div className="mt-4 grid gap-2 md:grid-cols-2">
            {[...board.have_details, ...board.need_details].map((item) => (
              <div
                key={item.id}
                className="rounded-lg border border-[var(--planner-board-border)] bg-[var(--planner-board-soft)] px-3 py-3"
              >
                <p className="text-[10px] font-semibold uppercase tracking-[0.14em] text-[var(--planner-board-muted-strong)]">
                  {item.label}
                </p>
                <p className="mt-1 text-sm font-medium text-[var(--planner-board-text)]">
                  {item.value || "Needed"}
                </p>
              </div>
            ))}
          </div>
        ) : null}
      </div>

      <div className="space-y-3">
        <p className="text-xs font-semibold uppercase tracking-[0.14em] text-[var(--planner-board-muted-strong)]">
          Choose the flight tradeoff
        </p>
        <div className="grid gap-4">
          {strategies.map((strategy) => (
            <button
              key={strategy.id}
              type="button"
              disabled={disabled}
              onClick={() =>
                onAction({
                  action_id: crypto.randomUUID(),
                  type: "select_flight_strategy",
                  flight_strategy: strategy.id,
                })
              }
              className={cn(
                "rounded-xl border px-5 py-4 text-left transition-colors",
                selectedStrategy === strategy.id
                  ? "border-[color:var(--accent)] bg-[var(--planner-board-card)]"
                  : "border-[var(--planner-board-border)] bg-[var(--planner-board-card)] hover:bg-[var(--planner-board-card-hover)]",
                disabled ? "cursor-wait opacity-70" : "cursor-pointer",
              )}
            >
              <div className="flex flex-wrap items-center gap-2">
                <h3 className="font-display text-lg font-bold text-[var(--planner-board-text)]">
                  {strategy.title}
                </h3>
                {strategy.recommended ? (
                  <span className="rounded-md bg-[var(--planner-board-soft)] px-2 py-1 text-[11px] font-semibold text-[var(--planner-board-accent-text)]">
                    Recommended
                  </span>
                ) : null}
                {selectedStrategy === strategy.id ? (
                  <span className="rounded-md border border-[color:var(--accent)] px-2 py-1 text-[11px] font-semibold text-[color:var(--accent)]">
                    Selected
                  </span>
                ) : null}
              </div>
              <p className="mt-2 text-sm leading-6 text-[var(--planner-board-muted)]">
                {strategy.description}
              </p>
              {strategy.bullets.length ? (
                <ul className="mt-3 grid gap-2">
                  {strategy.bullets.slice(0, 3).map((bullet) => (
                    <li
                      key={bullet}
                      className="flex items-start gap-2 text-xs leading-5 text-[var(--planner-board-muted)]"
                    >
                      <span className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-[color:var(--accent)]" />
                      <span>{bullet}</span>
                    </li>
                  ))}
                </ul>
              ) : null}
            </button>
          ))}
        </div>
      </div>

      {!blocked ? (
        <div className="grid gap-5 xl:grid-cols-2">
          <FlightOptionSection
            title="Outbound options"
            options={outboundOptions}
            selectedId={selectedOutboundId}
            disabled={disabled || selectedStrategy === "keep_flexible"}
            actionType="select_outbound_flight"
            onAction={onAction}
          />
          <FlightOptionSection
            title="Return options"
            options={returnOptions}
            selectedId={selectedReturnId}
            disabled={disabled || selectedStrategy === "keep_flexible"}
            actionType="select_return_flight"
            onAction={onAction}
          />
        </div>
      ) : null}

      {board.flight_downstream_notes?.length ? (
        <div className="rounded-xl border border-[var(--planner-board-border)] bg-[var(--planner-board-soft)] px-5 py-4">
          <p className="text-xs font-semibold uppercase tracking-[0.14em] text-[var(--planner-board-muted-strong)]">
            Planning notes
          </p>
          <div className="mt-3 space-y-2">
            {board.flight_downstream_notes.map((note) => (
              <p
                key={note}
                className="text-sm leading-6 text-[var(--planner-board-muted)]"
              >
                {note}
              </p>
            ))}
          </div>
        </div>
      ) : null}

      <div className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-[var(--planner-board-border)] bg-[var(--planner-board-card)] px-5 py-4">
        <div className="max-w-xl text-sm leading-6 text-[var(--planner-board-muted)]">
          <p>
            Confirm when the outbound and return shape is good enough for
            planning. Flights remain working choices for the itinerary.
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <button
            type="button"
            disabled={disabled || blocked}
            onClick={() =>
              onAction({
                action_id: crypto.randomUUID(),
                type: "keep_flights_open",
              })
            }
            className={cn(
              "rounded-md border px-4 py-2 text-xs font-semibold uppercase tracking-[0.14em] transition-colors",
              disabled || blocked
                ? "cursor-not-allowed border-[var(--planner-board-border)] text-[var(--planner-board-muted-strong)] opacity-60"
                : "border-[var(--planner-board-border)] text-[var(--planner-board-muted-strong)] hover:bg-[var(--planner-board-soft)]",
            )}
          >
            Keep flexible
          </button>
          <button
            type="button"
            disabled={disabled || !canConfirm}
            onClick={() =>
              onAction({
                action_id: crypto.randomUUID(),
                type: "confirm_flight_selection",
                flight_strategy: selectedStrategy,
              })
            }
            className={cn(
              "rounded-md border px-4 py-2 text-xs font-semibold uppercase tracking-[0.14em] transition-colors",
              disabled || !canConfirm
                ? "cursor-not-allowed border-[var(--planner-board-border)] text-[var(--planner-board-muted-strong)] opacity-60"
                : "border-[color:var(--accent)] bg-[color:var(--accent)] text-white hover:opacity-90",
            )}
          >
            Confirm flights
          </button>
        </div>
      </div>
    </div>
  );
}

function FlightOptionSection({
  title,
  options,
  selectedId,
  disabled,
  actionType,
  onAction,
}: {
  title: string;
  options: AdvancedFlightOptionCard[];
  selectedId: string | null;
  disabled: boolean;
  actionType: "select_outbound_flight" | "select_return_flight";
  onAction: (action: PlannerBoardActionIntent) => void;
}) {
  return (
    <section className="space-y-3">
      <p className="text-xs font-semibold uppercase tracking-[0.14em] text-[var(--planner-board-muted-strong)]">
        {title}
      </p>
      <div className="grid gap-3">
        {options.map((option) => (
          <FlightOptionCard
            key={option.id}
            option={option}
            selected={selectedId === option.id}
            disabled={disabled}
            actionType={actionType}
            onAction={onAction}
          />
        ))}
      </div>
    </section>
  );
}

function FlightOptionCard({
  option,
  selected,
  disabled,
  actionType,
  onAction,
}: {
  option: AdvancedFlightOptionCard;
  selected: boolean;
  disabled: boolean;
  actionType: "select_outbound_flight" | "select_return_flight";
  onAction: (action: PlannerBoardActionIntent) => void;
}) {
  return (
    <button
      type="button"
      disabled={disabled}
      onClick={() =>
        onAction({
          action_id: crypto.randomUUID(),
          type: actionType,
          flight_option_id: option.id,
        })
      }
      className={cn(
        "rounded-xl border bg-[var(--planner-board-card)] px-5 py-4 text-left transition-colors",
        selected
          ? "border-[color:var(--accent)]"
          : "border-[var(--planner-board-border)] hover:bg-[var(--planner-board-card-hover)]",
        disabled ? "cursor-not-allowed opacity-60" : "cursor-pointer",
      )}
    >
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-2">
            <span className="rounded-md bg-[var(--planner-board-soft)] px-2.5 py-1 text-[10px] font-semibold uppercase tracking-[0.14em] text-[var(--planner-board-muted-strong)]">
              {option.direction === "outbound" ? "Outbound" : "Return"}
            </span>
            {option.recommended ? (
              <span className="rounded-md bg-[color:color-mix(in_srgb,var(--accent)_10%,transparent)] px-2.5 py-1 text-[10px] font-semibold uppercase tracking-[0.14em] text-[color:var(--accent)]">
                Recommended
              </span>
            ) : null}
            {option.source_kind === "placeholder" ? (
              <span className="rounded-md border border-[var(--planner-board-border)] px-2.5 py-1 text-[10px] font-semibold uppercase tracking-[0.14em] text-[var(--planner-board-muted-strong)]">
                Placeholder
              </span>
            ) : null}
            {selected ? (
              <span className="rounded-md border border-[color:var(--accent)] px-2.5 py-1 text-[10px] font-semibold uppercase tracking-[0.14em] text-[color:var(--accent)]">
                Selected
              </span>
            ) : null}
          </div>
          <div className="mt-3 flex items-center gap-3">
            <div className="min-w-0">
              <p className="font-display text-lg font-bold text-[var(--planner-board-text)]">
                {option.departure_airport}
              </p>
              <p className="text-xs text-[var(--planner-board-muted)]">
                {formatFlightDateTime(option.departure_time) || "Time open"}
              </p>
            </div>
            <div className="flex flex-1 items-center gap-2 text-[var(--planner-board-muted)]">
              <Plane className="h-4 w-4 shrink-0 text-[color:var(--accent)]" />
              <div className="h-px flex-1 border-t border-dashed border-[var(--planner-board-border)]" />
              {option.duration_text ? (
                <span className="inline-flex items-center gap-1 text-xs">
                  <Clock className="h-3.5 w-3.5" />
                  {option.duration_text}
                </span>
              ) : null}
            </div>
            <div className="min-w-0 text-right">
              <p className="font-display text-lg font-bold text-[var(--planner-board-text)]">
                {option.arrival_airport}
              </p>
              <p className="text-xs text-[var(--planner-board-muted)]">
                {formatFlightDateTime(option.arrival_time) || "Arrival open"}
              </p>
            </div>
          </div>
          <p className="mt-3 text-sm leading-6 text-[var(--planner-board-muted)]">
            {option.summary}
          </p>
          <div className="mt-3 flex flex-wrap gap-2">
            {formatFlightStopLabel(option.stop_count) ? (
              <span className="rounded-md border border-[var(--planner-board-border)] px-2.5 py-1 text-[11px] font-semibold text-[var(--planner-board-muted-strong)]">
                {formatFlightStopLabel(option.stop_count)}
              </span>
            ) : null}
            {option.price_text ? (
              <span className="rounded-md border border-[var(--planner-board-border)] px-2.5 py-1 text-[11px] font-semibold text-[var(--planner-board-muted-strong)]">
                {option.price_text}
              </span>
            ) : null}
            {option.timing_quality ? (
              <span className="rounded-md border border-[var(--planner-board-border)] px-2.5 py-1 text-[11px] font-semibold text-[var(--planner-board-muted-strong)]">
                {option.timing_quality}
              </span>
            ) : null}
          </div>
          {option.layover_summary ? (
            <p className="mt-2 text-xs leading-5 text-[var(--planner-board-muted)]">
              {option.layover_summary}
            </p>
          ) : null}
          {option.legs?.length ? (
            <div className="mt-3 grid gap-2">
              {option.legs.slice(0, 3).map((leg, index) => (
                <div
                  key={`${option.id}-leg-${index}`}
                  className="rounded-md bg-[var(--planner-board-soft)] px-3 py-2 text-xs leading-5 text-[var(--planner-board-muted)]"
                >
                  <span className="font-semibold text-[var(--planner-board-text)]">
                    {leg.departure_airport} to {leg.arrival_airport}
                  </span>
                  {leg.carrier ? ` · ${leg.carrier}` : ""}
                  {leg.flight_number ? ` ${leg.flight_number}` : ""}
                  {leg.duration_text ? ` · ${leg.duration_text}` : ""}
                </div>
              ))}
            </div>
          ) : null}
          {option.tradeoffs.length ? (
            <div className="mt-3 flex flex-wrap gap-2">
              {option.tradeoffs.slice(0, 3).map((tradeoff) => (
                <span
                  key={tradeoff}
                  className="rounded-md bg-[var(--planner-board-soft)] px-2.5 py-1 text-[11px] font-medium text-[var(--planner-board-muted)]"
                >
                  {tradeoff}
                </span>
              ))}
            </div>
          ) : null}
          {option.inventory_notice ? (
            <p className="mt-3 text-xs leading-5 text-[var(--planner-board-muted)]">
              {option.inventory_notice}
            </p>
          ) : null}
        </div>
      </div>
    </button>
  );
}

function AdvancedActivitiesWorkspace({
  board,
  disabled,
  onAction,
}: {
  board: TripSuggestionBoardState;
  disabled: boolean;
  onAction: (action: PlannerBoardActionIntent) => void;
}) {
  const candidates = board.activity_candidates ?? [];
  const visibleCandidates = candidates.filter(
    (candidate) => candidate.disposition !== "pass",
  );
  const passedCandidates = candidates.filter(
    (candidate) => candidate.disposition === "pass",
  );
  const unscheduledCandidateIds = new Set(
    board.unscheduled_activity_candidate_ids ?? [],
  );
  const reservedCandidateIds = new Set(board.reserved_candidate_ids ?? []);
  const reservedCandidates = candidates.filter((candidate) =>
    reservedCandidateIds.has(candidate.id),
  );
  const overflowCandidates = candidates.filter(
    (candidate) =>
      unscheduledCandidateIds.has(candidate.id) &&
      !reservedCandidateIds.has(candidate.id),
  );
  const dayPlans = board.activity_day_plans ?? [];
  const scheduledBlocks = dayPlans.flatMap((dayPlan) =>
    dayPlan.blocks.filter((block) => Boolean(block.candidate_id)),
  );
  const scheduledBlockByCandidateId = new Map(
    scheduledBlocks
      .filter((block) => block.candidate_id)
      .map((block) => [block.candidate_id as string, block]),
  );
  const candidateLookup = new Map(candidates.map((candidate) => [candidate.id, candidate]));
  const activePool = visibleCandidates.filter(
    (candidate) => !reservedCandidateIds.has(candidate.id),
  );

  return (
    <div className="space-y-6">
      <div className="grid gap-3 md:grid-cols-3">
        <ActivityWorkspaceStat
          label="Leading picks"
          value={(board.essential_ids ?? []).length}
        />
        <ActivityWorkspaceStat
          label="In the mix"
          value={(board.maybe_ids ?? []).length}
        />
        <ActivityWorkspaceStat
          label="Left out"
          value={(board.passed_ids ?? []).length}
        />
      </div>

      <div className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-[var(--planner-board-border)] bg-[var(--planner-board-card)] px-5 py-4 text-sm leading-6 text-[var(--planner-board-muted)]">
        <div className="space-y-1">
          {board.activity_workspace_summary ? (
            <p>{board.activity_workspace_summary}</p>
          ) : null}
          {board.activity_schedule_summary ? (
            <p className="text-[var(--planner-board-muted-strong)]">
              {board.activity_schedule_summary}
            </p>
          ) : null}
          {board.weather_workspace_summary ? (
            <p>{board.weather_workspace_summary}</p>
          ) : null}
        </div>
        <button
          type="button"
          disabled={disabled}
          onClick={() =>
            onAction({
              action_id: crypto.randomUUID(),
              type: "rebuild_activity_day_plan",
            })
          }
          className={cn(
            "rounded-md border px-3 py-2 text-xs font-semibold uppercase tracking-[0.12em] transition-colors",
            disabled
              ? "cursor-wait border-[var(--planner-board-border)] text-[var(--planner-board-muted-strong)] opacity-70"
              : "border-[var(--planner-board-border)] text-[var(--planner-board-muted-strong)] hover:bg-[var(--planner-board-soft)]",
          )}
        >
          Refresh draft days
        </button>
      </div>

      {board.activity_schedule_notes?.length ? (
        <div className="space-y-2 rounded-xl border border-[var(--planner-board-border)] bg-[var(--planner-board-soft)] px-5 py-4">
          <p className="text-xs font-semibold uppercase tracking-[0.14em] text-[var(--planner-board-muted-strong)]">
            Rebalance notes
          </p>
          <div className="space-y-2">
            {board.activity_schedule_notes.map((note) => (
              <p
                key={note}
                className="text-sm leading-6 text-[var(--planner-board-muted)]"
              >
                {note}
              </p>
            ))}
          </div>
        </div>
      ) : null}

      {dayPlans.length ? (
        <div className="space-y-4">
          <p className="text-xs font-semibold uppercase tracking-[0.14em] text-[var(--planner-board-muted-strong)]">
            First draft of the days
          </p>
          <div className="grid gap-4 xl:grid-cols-2">
            {dayPlans.map((dayPlan) => (
              <ActivityDayPlanView
                key={dayPlan.id}
                dayPlan={dayPlan}
                allDayPlans={dayPlans}
                candidateLookup={candidateLookup}
                disabled={disabled}
                onAction={onAction}
              />
            ))}
          </div>
        </div>
      ) : null}

      {activePool.length ? (
        <div className="space-y-3">
          <p className="text-xs font-semibold uppercase tracking-[0.14em] text-[var(--planner-board-muted-strong)]">
            Candidate pool
          </p>
          <div className="grid gap-4">
            {activePool.map((candidate) => (
              <AdvancedActivityCandidateCardView
                key={candidate.id}
                candidate={candidate}
                dayPlans={dayPlans}
                scheduledBlock={scheduledBlockByCandidateId.get(candidate.id) ?? null}
                reserved={reservedCandidateIds.has(candidate.id)}
                disabled={disabled}
                onAction={onAction}
              />
            ))}
          </div>
        </div>
      ) : null}

      {reservedCandidates.length ? (
        <div className="space-y-3">
          <p className="text-xs font-semibold uppercase tracking-[0.14em] text-[var(--planner-board-muted-strong)]">
            Saved for later
          </p>
          <div className="grid gap-4">
            {reservedCandidates.map((candidate) => (
              <AdvancedActivityCandidateCardView
                key={candidate.id}
                candidate={candidate}
                dayPlans={dayPlans}
                scheduledBlock={scheduledBlockByCandidateId.get(candidate.id) ?? null}
                reserved
                disabled={disabled}
                onAction={onAction}
              />
            ))}
          </div>
        </div>
      ) : null}

      {overflowCandidates.length ? (
        <div className="space-y-3">
          <p className="text-xs font-semibold uppercase tracking-[0.14em] text-[var(--planner-board-muted-strong)]">
            Still not fitting cleanly
          </p>
          <div className="grid gap-3">
            {overflowCandidates.map((candidate) => (
              <AdvancedActivityCandidateCardView
                key={candidate.id}
                candidate={candidate}
                dayPlans={dayPlans}
                scheduledBlock={scheduledBlockByCandidateId.get(candidate.id) ?? null}
                disabled={disabled}
                onAction={onAction}
              />
            ))}
          </div>
        </div>
      ) : null}

      {passedCandidates.length ? (
        <div className="space-y-3">
          <p className="text-xs font-semibold uppercase tracking-[0.14em] text-[var(--planner-board-muted-strong)]">
            Left out for now
          </p>
          <div className="grid gap-3">
            {passedCandidates.map((candidate) => (
              <AdvancedActivityCandidateCardView
                key={candidate.id}
                candidate={candidate}
                dayPlans={dayPlans}
                scheduledBlock={scheduledBlockByCandidateId.get(candidate.id) ?? null}
                disabled={disabled}
                onAction={onAction}
              />
            ))}
          </div>
        </div>
      ) : null}
    </div>
  );
}

function AdvancedReviewWorkspace({
  board,
  disabled,
  onAction,
}: {
  board: TripSuggestionBoardState;
  disabled: boolean;
  onAction: (action: PlannerBoardActionIntent) => void;
}) {
  const sections = board.advanced_review_section_cards ?? [];
  const notes = board.advanced_review_notes ?? [];
  const decisionSignals = board.advanced_review_decision_signals ?? [];
  const conflicts = board.planner_conflicts ?? [];
  return (
    <div className="space-y-5">
      <div className="rounded-xl border border-[var(--planner-board-border)] bg-[var(--planner-board-card)] px-5 py-4">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.14em] text-[var(--planner-board-muted-strong)]">
              Working review
            </p>
            {board.advanced_review_summary ? (
              <p className="mt-2 text-sm leading-6 text-[var(--planner-board-muted)]">
                {board.advanced_review_summary}
              </p>
            ) : null}
          </div>
          <span
            className={cn(
              "rounded-full px-3 py-1 text-xs font-semibold uppercase tracking-[0.12em]",
              board.advanced_review_readiness_status === "needs_review"
                ? "bg-[var(--planner-board-soft)] text-[var(--planner-board-cta)]"
                : board.advanced_review_readiness_status === "ready"
                  ? "bg-[var(--planner-board-accent-soft)] text-[var(--planner-board-accent-text)]"
                  : "bg-[var(--planner-board-soft)] text-[var(--planner-board-muted-strong)]",
            )}
          >
            {formatReviewStatus(board.advanced_review_readiness_status)}
          </span>
        </div>
        <div className="mt-4 grid gap-3 sm:grid-cols-2">
          {board.advanced_review_completed_summary ? (
            <ReviewSummaryTile
              label="Selected"
              value={board.advanced_review_completed_summary}
            />
          ) : null}
          {board.advanced_review_open_summary ? (
            <ReviewSummaryTile
              label="Still flexible"
              value={board.advanced_review_open_summary}
            />
          ) : null}
        </div>
      </div>

      {decisionSignals.length ? (
        <div className="rounded-xl border border-[var(--planner-board-border)] bg-[var(--planner-board-card)] px-5 py-4">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.14em] text-[var(--planner-board-muted-strong)]">
                Decision sources
              </p>
              <p className="mt-2 text-sm leading-6 text-[var(--planner-board-muted)]">
                The review keeps track of what was directly chosen, inferred, or
                supplied by live planning data.
              </p>
            </div>
          </div>
          <div className="mt-4 grid gap-3 lg:grid-cols-2">
            {decisionSignals.map((signal) => (
              <AdvancedReviewDecisionSignalCard
                key={`${signal.id}-${signal.value_summary}`}
                signal={signal}
              />
            ))}
          </div>
        </div>
      ) : null}

      {conflicts.length ? (
        <div className="rounded-xl border border-[var(--planner-board-border)] bg-[var(--planner-board-card)] px-5 py-4">
          <p className="text-xs font-semibold uppercase tracking-[0.14em] text-[var(--planner-board-muted-strong)]">
            Planning tensions
          </p>
          <div className="mt-3 space-y-3">
            {conflicts.map((conflict) => (
              <AdvancedReviewConflictCard
                key={conflict.id}
                conflict={conflict}
                disabled={disabled}
                onAction={onAction}
              />
            ))}
          </div>
        </div>
      ) : null}

      {notes.length ? (
        <div className="rounded-xl border border-[var(--planner-board-border)] bg-[var(--planner-board-soft)] px-5 py-4">
          <p className="text-xs font-semibold uppercase tracking-[0.14em] text-[var(--planner-board-muted-strong)]">
            Worth reviewing
          </p>
          <div className="mt-3 space-y-2">
            {notes.map((note) => (
              <p key={note} className="text-sm leading-6 text-[var(--planner-board-muted)]">
                {note}
              </p>
            ))}
          </div>
        </div>
      ) : null}

      <div className="rounded-xl border border-[var(--planner-board-border)] bg-[var(--planner-board-card)] px-5 py-4">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div className="min-w-0 flex-1">
            <p className="text-xs font-semibold uppercase tracking-[0.14em] text-[var(--planner-board-muted-strong)]">
              Save brochure-ready version
            </p>
            <p className="mt-2 text-sm leading-6 text-[var(--planner-board-muted)]">
              {getAdvancedReviewFinalizationCopy(
                board.advanced_review_readiness_status,
              )}
            </p>
            <p className="mt-2 text-xs leading-5 text-[var(--planner-board-muted-strong)]">
              These are planning choices, not bookings. Finalizing saves this version
              to Saved Trips and keeps it ready for the brochure view.
            </p>
          </div>
          <button
            type="button"
            disabled={disabled}
            onClick={() =>
              onAction({
                action_id: crypto.randomUUID(),
                type: "finalize_advanced_plan",
              })
            }
            className={cn(
              "rounded-md px-4 py-2 text-xs font-semibold uppercase tracking-[0.12em] transition-colors",
              disabled
                ? "cursor-wait bg-[var(--planner-board-muted-strong)] text-[var(--planner-board-card)] opacity-70"
                : "bg-[var(--planner-board-cta)] text-white hover:bg-[var(--planner-board-cta-hover)]",
            )}
          >
            Save version
          </button>
        </div>
      </div>

      <div className="grid gap-4">
        {sections.map((section) => (
          <AdvancedReviewSection
            key={section.id}
            section={section}
            disabled={disabled}
            onAction={onAction}
          />
        ))}
      </div>
    </div>
  );
}

function AdvancedReviewConflictCard({
  conflict,
  disabled,
  onAction,
}: {
  conflict: PlannerConflictRecord;
  disabled: boolean;
  onAction: (action: PlannerBoardActionIntent) => void;
}) {
  const revisionAnchor = getConflictRevisionAnchor(conflict);
  return (
    <article className="rounded-lg border border-[var(--planner-board-border)] bg-[var(--planner-board-soft)] px-4 py-3">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-2">
            <span
              className={cn(
                "rounded-full px-2.5 py-1 text-[10px] font-semibold uppercase tracking-[0.12em]",
                getConflictBadgeClass(conflict.severity),
              )}
            >
              {formatConflictSeverity(conflict.severity)}
            </span>
            {conflict.affected_areas.length ? (
              <p className="text-[11px] font-semibold uppercase tracking-[0.12em] text-[var(--planner-board-muted-strong)]">
                {conflict.affected_areas.join(" / ")}
              </p>
            ) : null}
          </div>
          <p className="mt-2 text-sm font-semibold leading-6 text-[var(--planner-board-foreground)]">
            {conflict.summary}
          </p>
          <p className="mt-1 text-xs leading-5 text-[var(--planner-board-muted)]">
            {conflict.suggested_repair}
          </p>
          {conflict.evidence.length ? (
            <div className="mt-2 space-y-1">
              {conflict.evidence.slice(0, 2).map((item) => (
                <p
                  key={item}
                  className="text-xs leading-5 text-[var(--planner-board-muted-strong)]"
                >
                  {item}
                </p>
              ))}
            </div>
          ) : null}
        </div>
        {revisionAnchor ? (
          <button
            type="button"
            disabled={disabled}
            onClick={() =>
              onAction({
                action_id: crypto.randomUUID(),
                type: "revise_advanced_review_section",
                advanced_anchor: revisionAnchor,
              })
            }
            className={cn(
              "rounded-md border px-3 py-2 text-xs font-semibold uppercase tracking-[0.12em] transition-colors",
              disabled
                ? "cursor-wait border-[var(--planner-board-border)] text-[var(--planner-board-muted-strong)] opacity-70"
                : "border-[var(--planner-board-border)] text-[var(--planner-board-muted-strong)] hover:bg-[var(--planner-board-card)]",
            )}
          >
            Review
          </button>
        ) : null}
      </div>
    </article>
  );
}

function getConflictRevisionAnchor(
  conflict: PlannerConflictRecord,
): PlannerAdvancedAnchor | null {
  if (
    conflict.revision_target === "flight" ||
    conflict.revision_target === "stay" ||
    conflict.revision_target === "trip_style" ||
    conflict.revision_target === "activities"
  ) {
    return conflict.revision_target;
  }
  return null;
}

function formatConflictSeverity(severity: PlannerConflictRecord["severity"]) {
  if (severity === "important") {
    return "Important";
  }
  if (severity === "info") {
    return "Note";
  }
  return "Worth resolving";
}

function getConflictBadgeClass(severity: PlannerConflictRecord["severity"]) {
  if (severity === "important") {
    return "bg-[var(--planner-board-card)] text-[var(--planner-board-cta)]";
  }
  if (severity === "info") {
    return "bg-[var(--planner-board-card)] text-[var(--planner-board-muted-strong)]";
  }
  return "bg-[var(--planner-board-accent-soft)] text-[var(--planner-board-accent-text)]";
}

function AdvancedReviewDecisionSignalCard({
  signal,
}: {
  signal: AdvancedReviewDecisionSignal;
}) {
  return (
    <div className="rounded-lg border border-[var(--planner-board-border)] bg-[var(--planner-board-soft)] px-4 py-3">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <p className="text-xs font-semibold uppercase tracking-[0.12em] text-[var(--planner-board-muted-strong)]">
          {signal.title}
        </p>
        <span
          className={cn(
            "rounded-full px-2.5 py-1 text-[10px] font-semibold uppercase tracking-[0.12em]",
            getDecisionSignalBadgeClass(signal.confidence),
          )}
        >
          {signal.confidence_label}
        </span>
      </div>
      <p className="mt-2 text-sm font-semibold text-[var(--planner-board-foreground)]">
        {signal.value_summary}
      </p>
      <p className="mt-1 text-xs leading-5 text-[var(--planner-board-muted-strong)]">
        {signal.source_label} / {formatDecisionSignalStatus(signal.status)}
      </p>
      {signal.note ? (
        <p className="mt-2 text-xs leading-5 text-[var(--planner-board-muted)]">
          {signal.note}
        </p>
      ) : null}
    </div>
  );
}

function formatDecisionSignalStatus(
  status: AdvancedReviewDecisionSignal["status"],
) {
  if (status === "needs_review") {
    return "Worth reviewing";
  }
  if (status === "confirmed") {
    return "Selected";
  }
  if (status === "superseded") {
    return "Updated";
  }
  return "Working";
}

function getDecisionSignalBadgeClass(
  confidence: AdvancedReviewDecisionSignal["confidence"],
) {
  if (confidence === "high") {
    return "bg-[var(--planner-board-accent-soft)] text-[var(--planner-board-accent-text)]";
  }
  if (confidence === "low") {
    return "bg-[var(--planner-board-card)] text-[var(--planner-board-cta)]";
  }
  return "bg-[var(--planner-board-card)] text-[var(--planner-board-muted-strong)]";
}

function getAdvancedReviewFinalizationCopy(
  status: TripSuggestionBoardState["advanced_review_readiness_status"],
) {
  if (status === "needs_review") {
    return "Worth reviewing items will be saved with caution notes unless you revise first.";
  }
  if (status === "flexible") {
    return "Some choices are intentionally flexible and will be captured that way.";
  }
  return "Ready to save as brochure-ready.";
}

function ReviewSummaryTile({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg bg-[var(--planner-board-soft)] px-4 py-3">
      <p className="text-[10px] font-semibold uppercase tracking-[0.14em] text-[var(--planner-board-muted-strong)]">
        {label}
      </p>
      <p className="mt-1 text-sm leading-6 text-[var(--planner-board-muted)]">
        {value}
      </p>
    </div>
  );
}

function AdvancedReviewSection({
  section,
  disabled,
  onAction,
}: {
  section: AdvancedReviewSectionCard;
  disabled: boolean;
  onAction: (action: PlannerBoardActionIntent) => void;
}) {
  return (
    <article className="rounded-xl border border-[var(--planner-board-border)] bg-[var(--planner-board-card)] px-5 py-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-2">
            <h3 className="font-display text-lg font-bold text-[var(--planner-board-text)]">
              {section.title}
            </h3>
            <span
              className={cn(
                "rounded-full px-2.5 py-1 text-[10px] font-semibold uppercase tracking-[0.12em]",
                section.status === "needs_review"
                  ? "bg-[var(--planner-board-soft)] text-[var(--planner-board-cta)]"
                  : section.status === "ready"
                    ? "bg-[var(--planner-board-accent-soft)] text-[var(--planner-board-accent-text)]"
                    : "bg-[var(--planner-board-soft)] text-[var(--planner-board-muted-strong)]",
              )}
            >
              {formatReviewStatus(section.status)}
            </span>
          </div>
          <p className="mt-2 text-sm leading-6 text-[var(--planner-board-muted)]">
            {section.summary}
          </p>
        </div>
        {section.revision_anchor ? (
          <button
            type="button"
            disabled={disabled}
            onClick={() =>
              onAction({
                action_id: crypto.randomUUID(),
                type: "revise_advanced_review_section",
                advanced_anchor: section.revision_anchor as PlannerAdvancedAnchor,
              })
            }
            className={cn(
              "rounded-md border px-3 py-2 text-xs font-semibold uppercase tracking-[0.12em] transition-colors",
              disabled
                ? "cursor-wait border-[var(--planner-board-border)] text-[var(--planner-board-muted-strong)] opacity-70"
                : "border-[var(--planner-board-border)] text-[var(--planner-board-muted-strong)] hover:bg-[var(--planner-board-soft)]",
            )}
          >
            {section.cta_label || "Review"}
          </button>
        ) : null}
      </div>
      {section.notes.length ? (
        <div className="mt-4 space-y-2 border-t border-[var(--planner-board-border)] pt-4">
          {section.notes.map((note) => (
            <p key={note} className="text-sm leading-6 text-[var(--planner-board-muted)]">
              {note}
            </p>
          ))}
        </div>
      ) : null}
    </article>
  );
}

function AdvancedTripStyleWorkspace({
  board,
  disabled,
  onAction,
}: {
  board: TripSuggestionBoardState;
  disabled: boolean;
  onAction: (action: PlannerBoardActionIntent) => void;
}) {
  const recommendedPrimaries = board.trip_style_recommended_primaries ?? [];
  const recommendedAccents = board.trip_style_recommended_accents ?? [];
  const selectedPrimary = board.selected_trip_style_primary ?? null;
  const selectedAccent = board.selected_trip_style_accent ?? null;
  const primaryOptions: PlannerTripDirectionPrimary[] = [
    "food_led",
    "culture_led",
    "nightlife_led",
    "outdoors_led",
    "balanced",
  ];
  const accentOptions: PlannerTripDirectionAccent[] = [
    "local",
    "classic",
    "polished",
    "romantic",
    "relaxed",
  ];

  return (
    <div className="space-y-6">
      <div className="rounded-xl border border-[var(--planner-board-border)] bg-[var(--planner-board-card)] px-5 py-4 text-sm leading-6 text-[var(--planner-board-muted)]">
        {board.trip_style_workspace_summary ? (
          <p>{board.trip_style_workspace_summary}</p>
        ) : null}
        {board.trip_style_selection_rationale ? (
          <p className="mt-2 text-[var(--planner-board-muted-strong)]">
            {board.trip_style_selection_rationale}
          </p>
        ) : null}
        {board.trip_style_downstream_influence_summary ? (
          <p className="mt-2">{board.trip_style_downstream_influence_summary}</p>
        ) : null}
      </div>

      <div className="space-y-3">
        <p className="text-xs font-semibold uppercase tracking-[0.14em] text-[var(--planner-board-muted-strong)]">
          Choose the main direction
        </p>
        <div className="grid gap-4">
          {primaryOptions.map((primary) => (
            <button
              key={primary}
              type="button"
              disabled={disabled}
              onClick={() =>
                onAction({
                  action_id: crypto.randomUUID(),
                  type: "select_trip_style_direction_primary",
                  trip_style_direction_primary: primary,
                })
              }
              className={cn(
                "rounded-xl border px-5 py-4 text-left transition-colors",
                selectedPrimary === primary
                  ? "border-[color:var(--accent)] bg-[var(--planner-board-card)]"
                  : "border-[var(--planner-board-border)] bg-[var(--planner-board-card)] hover:bg-[var(--planner-board-card-hover)]",
                disabled ? "cursor-wait opacity-70" : "cursor-pointer",
              )}
            >
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <div className="flex flex-wrap items-center gap-2">
                    <h3 className="font-display text-lg font-bold text-[var(--planner-board-text)]">
                      {formatTripDirectionPrimaryLabel(primary)}
                    </h3>
                    {recommendedPrimaries.includes(primary) ? (
                      <span className="rounded-md bg-[var(--planner-board-soft)] px-2 py-1 text-[11px] font-semibold text-[var(--planner-board-accent-text)]">
                        Recommended
                      </span>
                    ) : null}
                    {selectedPrimary === primary ? (
                      <span className="rounded-md border border-[color:var(--accent)] px-2 py-1 text-[11px] font-semibold text-[color:var(--accent)]">
                        Selected
                      </span>
                    ) : null}
                  </div>
                  <p className="mt-2 text-sm leading-6 text-[var(--planner-board-muted)]">
                    {tripDirectionPrimaryDescription(primary)}
                  </p>
                </div>
              </div>
            </button>
          ))}
        </div>
      </div>

      <div className="space-y-3">
        <div className="flex items-center justify-between gap-3">
          <p className="text-xs font-semibold uppercase tracking-[0.14em] text-[var(--planner-board-muted-strong)]">
            Optional accent
          </p>
          {selectedAccent ? (
            <button
              type="button"
              disabled={disabled}
              onClick={() =>
                onAction({
                  action_id: crypto.randomUUID(),
                  type: "clear_trip_style_direction_accent",
                })
              }
              className={cn(
                "rounded-md border px-3 py-2 text-[11px] font-semibold uppercase tracking-[0.12em] transition-colors",
                disabled
                  ? "cursor-wait border-[var(--planner-board-border)] text-[var(--planner-board-muted-strong)] opacity-70"
                  : "border-[var(--planner-board-border)] text-[var(--planner-board-muted-strong)] hover:bg-[var(--planner-board-soft)]",
              )}
            >
              Clear accent
            </button>
          ) : null}
        </div>
        <div className="grid gap-3 md:grid-cols-2">
          {accentOptions.map((accent) => (
            <button
              key={accent}
              type="button"
              disabled={disabled}
              onClick={() =>
                onAction({
                  action_id: crypto.randomUUID(),
                  type: "select_trip_style_direction_accent",
                  trip_style_direction_accent: accent,
                })
              }
              className={cn(
                "rounded-xl border px-4 py-4 text-left transition-colors",
                selectedAccent === accent
                  ? "border-[color:var(--accent)] bg-[var(--planner-board-card)]"
                  : "border-[var(--planner-board-border)] bg-[var(--planner-board-card)] hover:bg-[var(--planner-board-card-hover)]",
                disabled ? "cursor-wait opacity-70" : "cursor-pointer",
              )}
            >
              <div className="flex flex-wrap items-center gap-2">
                <p className="font-semibold text-[var(--planner-board-text)]">
                  {formatTripDirectionAccentLabel(accent)}
                </p>
                {recommendedAccents.includes(accent) ? (
                  <span className="rounded-md bg-[var(--planner-board-soft)] px-2 py-1 text-[11px] font-semibold text-[var(--planner-board-accent-text)]">
                    Recommended
                  </span>
                ) : null}
                {selectedAccent === accent ? (
                  <span className="rounded-md border border-[color:var(--accent)] px-2 py-1 text-[11px] font-semibold text-[color:var(--accent)]">
                    Selected
                  </span>
                ) : null}
              </div>
              <p className="mt-2 text-sm leading-6 text-[var(--planner-board-muted)]">
                {tripDirectionAccentDescription(accent)}
              </p>
            </button>
          ))}
        </div>
      </div>

      <div className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-[var(--planner-board-border)] bg-[var(--planner-board-card)] px-5 py-4">
        <div className="text-sm leading-6 text-[var(--planner-board-muted)]">
          {board.trip_style_completion_summary ? (
            <p>{board.trip_style_completion_summary}</p>
          ) : (
            <p>
              Confirm the main direction when it feels right, and Wandrix will
              use it as the strongest input for Activities next.
            </p>
          )}
        </div>
        <button
          type="button"
          disabled={disabled || !selectedPrimary}
          onClick={() =>
            onAction({
              action_id: crypto.randomUUID(),
              type: "confirm_trip_style_direction",
              trip_style_direction_primary: selectedPrimary,
              trip_style_direction_accent: selectedAccent,
            })
          }
          className={cn(
            "rounded-md border px-4 py-2 text-xs font-semibold uppercase tracking-[0.14em] transition-colors",
            disabled || !selectedPrimary
              ? "cursor-not-allowed border-[var(--planner-board-border)] text-[var(--planner-board-muted-strong)] opacity-60"
              : "border-[color:var(--accent)] bg-[color:var(--accent)] text-white hover:opacity-90",
          )}
        >
          Confirm direction
        </button>
      </div>
    </div>
  );
}

function AdvancedTripStylePaceWorkspace({
  board,
  disabled,
  onAction,
}: {
  board: TripSuggestionBoardState;
  disabled: boolean;
  onAction: (action: PlannerBoardActionIntent) => void;
}) {
  const recommendedPaces = board.trip_style_recommended_paces ?? [];
  const selectedPace = board.selected_trip_style_pace ?? null;
  const selectedPrimary = board.selected_trip_style_primary ?? null;
  const selectedAccent = board.selected_trip_style_accent ?? null;
  const paceOptions: PlannerTripPace[] = ["slow", "balanced", "full"];
  const directionLabel = selectedPrimary
    ? formatTripDirectionPrimaryLabel(selectedPrimary)
    : "Balanced";
  const accentLabel = selectedAccent
    ? ` with a ${formatTripDirectionAccentLabel(selectedAccent).toLowerCase()} accent`
    : "";

  return (
    <div className="space-y-6">
      <div className="rounded-xl border border-[var(--planner-board-border)] bg-[var(--planner-board-card)] px-5 py-4">
        <p className="text-xs font-semibold uppercase tracking-[0.14em] text-[var(--planner-board-muted-strong)]">
          Current trip character
        </p>
        <p className="mt-2 font-display text-xl font-bold text-[var(--planner-board-text)]">
          {directionLabel}
          {accentLabel}
        </p>
        {board.trip_style_downstream_influence_summary ? (
          <p className="mt-2 text-sm leading-6 text-[var(--planner-board-muted)]">
            {board.trip_style_downstream_influence_summary}
          </p>
        ) : null}
      </div>

      <div className="space-y-3">
        <p className="text-xs font-semibold uppercase tracking-[0.14em] text-[var(--planner-board-muted-strong)]">
          Choose the pace
        </p>
        <div className="grid gap-4">
          {paceOptions.map((pace) => (
            <button
              key={pace}
              type="button"
              disabled={disabled}
              onClick={() =>
                onAction({
                  action_id: crypto.randomUUID(),
                  type: "select_trip_style_pace",
                  trip_style_pace: pace,
                })
              }
              className={cn(
                "rounded-xl border px-5 py-4 text-left transition-colors",
                selectedPace === pace
                  ? "border-[color:var(--accent)] bg-[var(--planner-board-card)]"
                  : "border-[var(--planner-board-border)] bg-[var(--planner-board-card)] hover:bg-[var(--planner-board-card-hover)]",
                disabled ? "cursor-wait opacity-70" : "cursor-pointer",
              )}
            >
              <div className="flex flex-wrap items-center gap-2">
                <h3 className="font-display text-lg font-bold text-[var(--planner-board-text)]">
                  {formatTripPaceLabel(pace)}
                </h3>
                {recommendedPaces.includes(pace) ? (
                  <span className="rounded-md bg-[var(--planner-board-soft)] px-2 py-1 text-[11px] font-semibold text-[var(--planner-board-accent-text)]">
                    Recommended
                  </span>
                ) : null}
                {selectedPace === pace ? (
                  <span className="rounded-md border border-[color:var(--accent)] px-2 py-1 text-[11px] font-semibold text-[color:var(--accent)]">
                    Selected
                  </span>
                ) : null}
              </div>
              <p className="mt-2 text-sm leading-6 text-[var(--planner-board-muted)]">
                {tripPaceDescription(pace)}
              </p>
            </button>
          ))}
        </div>
      </div>

      <div className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-[var(--planner-board-border)] bg-[var(--planner-board-card)] px-5 py-4">
        <div className="max-w-xl text-sm leading-6 text-[var(--planner-board-muted)]">
          {board.trip_style_pace_rationale ? (
            <p>{board.trip_style_pace_rationale}</p>
          ) : (
            <p>
              Confirm the pace when it feels right, and Activities will inherit
              both the trip character and day density.
            </p>
          )}
          {board.trip_style_pace_downstream_influence_summary ? (
            <p className="mt-2">{board.trip_style_pace_downstream_influence_summary}</p>
          ) : null}
        </div>
        <button
          type="button"
          disabled={disabled || !selectedPace}
          onClick={() =>
            onAction({
              action_id: crypto.randomUUID(),
              type: "confirm_trip_style_pace",
              trip_style_pace: selectedPace,
            })
          }
          className={cn(
            "rounded-md border px-4 py-2 text-xs font-semibold uppercase tracking-[0.14em] transition-colors",
            disabled || !selectedPace
              ? "cursor-not-allowed border-[var(--planner-board-border)] text-[var(--planner-board-muted-strong)] opacity-60"
              : "border-[color:var(--accent)] bg-[color:var(--accent)] text-white hover:opacity-90",
          )}
        >
          Confirm pace
        </button>
      </div>
    </div>
  );
}

function AdvancedTripStyleTradeoffsWorkspace({
  board,
  disabled,
  onAction,
}: {
  board: TripSuggestionBoardState;
  disabled: boolean;
  onAction: (action: PlannerBoardActionIntent) => void;
}) {
  const tradeoffCards = board.trip_style_recommended_tradeoff_cards ?? [];
  const selectedTradeoffs = board.selected_trip_style_tradeoffs ?? [];
  const selectedPrimary = board.selected_trip_style_primary ?? null;
  const selectedAccent = board.selected_trip_style_accent ?? null;
  const selectedPace = board.selected_trip_style_pace ?? null;
  const selectedByAxis = new Map(
    selectedTradeoffs.map((decision) => [
      decision.axis,
      decision.selected_value,
    ]),
  );
  const directionLabel = selectedPrimary
    ? formatTripDirectionPrimaryLabel(selectedPrimary)
    : "Balanced";
  const accentLabel = selectedAccent
    ? ` with a ${formatTripDirectionAccentLabel(selectedAccent).toLowerCase()} accent`
    : "";
  const paceLabel = selectedPace
    ? ` at a ${formatTripPaceLabel(selectedPace).toLowerCase()} pace`
    : "";

  return (
    <div className="space-y-6">
      <div className="rounded-xl border border-[var(--planner-board-border)] bg-[var(--planner-board-card)] px-5 py-4">
        <p className="text-xs font-semibold uppercase tracking-[0.14em] text-[var(--planner-board-muted-strong)]">
          Current trip character
        </p>
        <p className="mt-2 font-display text-xl font-bold text-[var(--planner-board-text)]">
          {directionLabel}
          {accentLabel}
          {paceLabel}
        </p>
        {board.trip_style_pace_downstream_influence_summary ? (
          <p className="mt-2 text-sm leading-6 text-[var(--planner-board-muted)]">
            {board.trip_style_pace_downstream_influence_summary}
          </p>
        ) : null}
      </div>

      <div className="space-y-4">
        {tradeoffCards.map((card) => {
          const selectedValue = selectedByAxis.get(card.axis);
          return (
            <article
              key={card.axis}
              className="rounded-xl border border-[var(--planner-board-border)] bg-[var(--planner-board-card)] px-5 py-4"
            >
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <p className="text-xs font-semibold uppercase tracking-[0.14em] text-[var(--planner-board-muted-strong)]">
                    {formatTripTradeoffAxisLabel(card.axis)}
                  </p>
                  <h3 className="mt-1 font-display text-lg font-bold text-[var(--planner-board-text)]">
                    {card.title}
                  </h3>
                </div>
              </div>
              <p className="mt-2 text-sm leading-6 text-[var(--planner-board-muted)]">
                {card.description}
              </p>
              <div className="mt-4 grid gap-3 md:grid-cols-3">
                {card.options.map((option) => (
                  <button
                    key={option.value}
                    type="button"
                    disabled={disabled}
                    onClick={() =>
                      onAction({
                        action_id: crypto.randomUUID(),
                        type: "set_trip_style_tradeoff",
                        trip_style_tradeoff_axis: card.axis,
                        trip_style_tradeoff_value: option.value,
                      })
                    }
                    className={cn(
                      "rounded-xl border px-4 py-4 text-left transition-colors",
                      selectedValue === option.value
                        ? "border-[color:var(--accent)] bg-[var(--planner-board-card)]"
                        : "border-[var(--planner-board-border)] bg-[var(--planner-board-card)] hover:bg-[var(--planner-board-card-hover)]",
                      disabled ? "cursor-wait opacity-70" : "cursor-pointer",
                    )}
                  >
                    <div className="flex flex-wrap items-center gap-2">
                      <p className="font-semibold text-[var(--planner-board-text)]">
                        {option.label}
                      </p>
                      {option.recommended ? (
                        <span className="rounded-md bg-[var(--planner-board-soft)] px-2 py-1 text-[11px] font-semibold text-[var(--planner-board-accent-text)]">
                          Recommended
                        </span>
                      ) : null}
                      {selectedValue === option.value ? (
                        <span className="rounded-md border border-[color:var(--accent)] px-2 py-1 text-[11px] font-semibold text-[color:var(--accent)]">
                          Selected
                        </span>
                      ) : null}
                    </div>
                    <p className="mt-2 text-sm leading-6 text-[var(--planner-board-muted)]">
                      {option.description}
                    </p>
                  </button>
                ))}
              </div>
            </article>
          );
        })}
      </div>

      <div className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-[var(--planner-board-border)] bg-[var(--planner-board-card)] px-5 py-4">
        <div className="max-w-xl text-sm leading-6 text-[var(--planner-board-muted)]">
          {board.trip_style_tradeoff_rationale ? (
            <p>{board.trip_style_tradeoff_rationale}</p>
          ) : (
            <p>
              Confirm these tie-breakers when they feel right, and Activities
              will inherit the full Trip Style.
            </p>
          )}
          {board.trip_style_tradeoff_downstream_influence_summary ? (
            <p className="mt-2">
              {board.trip_style_tradeoff_downstream_influence_summary}
            </p>
          ) : null}
        </div>
        <button
          type="button"
          disabled={disabled || tradeoffCards.length === 0}
          onClick={() =>
            onAction({
              action_id: crypto.randomUUID(),
              type: "confirm_trip_style_tradeoffs",
            })
          }
          className={cn(
            "rounded-md border px-4 py-2 text-xs font-semibold uppercase tracking-[0.14em] transition-colors",
            disabled || tradeoffCards.length === 0
              ? "cursor-not-allowed border-[var(--planner-board-border)] text-[var(--planner-board-muted-strong)] opacity-60"
              : "border-[color:var(--accent)] bg-[color:var(--accent)] text-white hover:opacity-90",
          )}
        >
          Confirm tradeoffs
        </button>
      </div>
    </div>
  );
}

function ActivityDayPlanView({
  dayPlan,
  allDayPlans,
  candidateLookup,
  disabled,
  onAction,
}: {
  dayPlan: NonNullable<TripSuggestionBoardState["activity_day_plans"]>[number];
  allDayPlans: NonNullable<TripSuggestionBoardState["activity_day_plans"]>;
  candidateLookup: Map<string, AdvancedActivityCandidateCard>;
  disabled: boolean;
  onAction: (action: PlannerBoardActionIntent) => void;
}) {
  return (
    <section className="rounded-xl border border-[var(--planner-board-border)] bg-[var(--planner-board-card)] px-5 py-5 shadow-[0_1px_1px_rgba(0,0,0,0.04),0_8px_18px_rgba(0,0,0,0.04)]">
      <div className="flex items-baseline justify-between gap-3">
        <h3 className="font-display text-lg font-bold text-[var(--planner-board-text)]">
          {dayPlan.day_label}
        </h3>
        {dayPlan.date ? (
          <span className="text-xs font-semibold uppercase tracking-[0.12em] text-[var(--planner-board-muted-strong)]">
            {new Date(dayPlan.date).toLocaleDateString(undefined, {
              month: "short",
              day: "numeric",
            })}
          </span>
        ) : null}
      </div>

      <div className="mt-4 space-y-3">
        {dayPlan.blocks.length ? (
          dayPlan.blocks.map((block) => (
            <ActivityTimelineBlockView
              key={block.id}
              block={block}
              candidate={
                block.candidate_id ? candidateLookup.get(block.candidate_id) ?? null : null
              }
              allDayPlans={allDayPlans}
              disabled={disabled}
              onAction={onAction}
            />
          ))
        ) : (
          <p className="text-sm leading-6 text-[var(--planner-board-muted)]">
            This day still has room to take on more shape.
          </p>
        )}
      </div>
    </section>
  );
}

function ActivityTimelineBlockView({
  block,
  candidate,
  allDayPlans,
  disabled,
  onAction,
}: {
  block: NonNullable<
    NonNullable<TripSuggestionBoardState["activity_day_plans"]>[number]["blocks"]
  >[number];
  candidate: AdvancedActivityCandidateCard | null;
  allDayPlans: NonNullable<TripSuggestionBoardState["activity_day_plans"]>;
  disabled: boolean;
  onAction: (action: PlannerBoardActionIntent) => void;
}) {
  const blockLabel =
    block.type === "transfer"
      ? "Travel"
      : block.type === "event"
        ? "Timed moment"
        : "Planned stop";
  const timingLabel =
    block.start_at && block.end_at
      ? `${new Date(block.start_at).toLocaleTimeString(undefined, {
          hour: "numeric",
          minute: "2-digit",
        })} - ${new Date(block.end_at).toLocaleTimeString(undefined, {
          hour: "numeric",
          minute: "2-digit",
        })}`
      : null;
  const tone =
    block.type === "transfer"
      ? "bg-[var(--planner-board-soft)] text-[var(--planner-board-muted-strong)]"
      : block.type === "event"
        ? "bg-[color:color-mix(in_srgb,var(--accent)_10%,transparent)] text-[color:var(--accent)]"
        : "bg-[var(--planner-board-soft)] text-[var(--planner-board-accent-text)]";

  return (
    <article className="rounded-lg border border-[var(--planner-board-border)] px-4 py-3">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-2">
            <span
              className={cn(
                "rounded-md px-2.5 py-1 text-[10px] font-semibold uppercase tracking-[0.14em]",
                tone,
              )}
            >
              {blockLabel}
            </span>
            {block.fixed_time ? (
              <span className="rounded-md border border-[var(--planner-board-border)] px-2.5 py-1 text-[10px] font-semibold uppercase tracking-[0.14em] text-[var(--planner-board-muted-strong)]">
                Set time
              </span>
            ) : null}
            {block.manual_override ? (
              <span className="rounded-md border border-[color:var(--accent)] px-2.5 py-1 text-[10px] font-semibold uppercase tracking-[0.14em] text-[color:var(--accent)]">
                Pinned
              </span>
            ) : null}
          </div>
          <h4 className="mt-2 font-semibold text-[var(--planner-board-text)]">
            {block.title}
          </h4>
          <div className="mt-2 flex flex-wrap gap-3 text-xs text-[var(--planner-board-muted)]">
            {timingLabel ? (
              <span className="inline-flex items-center gap-1.5">
                <CalendarRange className="h-3.5 w-3.5" />
                {timingLabel}
              </span>
            ) : null}
            {block.location_label ? (
              <span className="inline-flex items-center gap-1.5">
                <MapPin className="h-3.5 w-3.5" />
                {block.location_label}
              </span>
            ) : null}
          </div>
          {block.summary ? (
            <p className="mt-2 text-sm leading-6 text-[var(--planner-board-muted)]">
              {block.summary}
            </p>
          ) : null}
          {(block.status_text || block.price_text || block.availability_text) ? (
            <div className="mt-3 flex flex-wrap gap-2">
              {[block.status_text, block.price_text, block.availability_text]
                .filter(Boolean)
                .map((detail) => (
                  <span
                    key={detail}
                    className="rounded-md bg-[var(--planner-board-soft)] px-2.5 py-1 text-[11px] font-medium text-[var(--planner-board-muted)]"
                  >
                    {detail}
                  </span>
                ))}
            </div>
          ) : null}
          {block.type === "event" && block.source_url ? (
            <a
              href={block.source_url}
              target="_blank"
              rel="noreferrer"
              className="mt-3 inline-flex items-center gap-1.5 text-xs font-semibold text-[color:var(--accent)] hover:underline"
            >
              View event
              <ExternalLink className="h-3.5 w-3.5" />
            </a>
          ) : null}
          {candidate ? (
            <div className="mt-4 flex flex-wrap gap-2">
              {!block.fixed_time ? (
                <>
                  <button
                    type="button"
                    disabled={disabled}
                    onClick={() =>
                      onAction({
                        action_id: crypto.randomUUID(),
                        type: "move_activity_candidate_earlier",
                        activity_candidate_id: candidate.id,
                        activity_candidate_title: candidate.title,
                        activity_candidate_kind: candidate.kind,
                      })
                    }
                    className={cn(
                      "rounded-md border px-3 py-2 text-[11px] font-semibold uppercase tracking-[0.12em] transition-colors",
                      disabled
                        ? "cursor-wait border-[var(--planner-board-border)] text-[var(--planner-board-muted-strong)] opacity-70"
                        : "border-[var(--planner-board-border)] text-[var(--planner-board-muted-strong)] hover:bg-[var(--planner-board-soft)]",
                    )}
                  >
                    Earlier
                  </button>
                  <button
                    type="button"
                    disabled={disabled}
                    onClick={() =>
                      onAction({
                        action_id: crypto.randomUUID(),
                        type: "move_activity_candidate_later",
                        activity_candidate_id: candidate.id,
                        activity_candidate_title: candidate.title,
                        activity_candidate_kind: candidate.kind,
                      })
                    }
                    className={cn(
                      "rounded-md border px-3 py-2 text-[11px] font-semibold uppercase tracking-[0.12em] transition-colors",
                      disabled
                        ? "cursor-wait border-[var(--planner-board-border)] text-[var(--planner-board-muted-strong)] opacity-70"
                        : "border-[var(--planner-board-border)] text-[var(--planner-board-muted-strong)] hover:bg-[var(--planner-board-soft)]",
                    )}
                  >
                    Later
                  </button>
                </>
              ) : null}
              {allDayPlans
                .filter((plan) => plan.day_index !== block.day_index)
                .map((plan) => (
                  <button
                    key={plan.id}
                    type="button"
                    disabled={disabled || block.fixed_time}
                    onClick={() =>
                      onAction({
                        action_id: crypto.randomUUID(),
                        type: "move_activity_candidate_to_day",
                        activity_candidate_id: candidate.id,
                        activity_candidate_title: candidate.title,
                        activity_candidate_kind: candidate.kind,
                        activity_target_day_index: plan.day_index,
                      })
                    }
                    className={cn(
                      "rounded-md border px-3 py-2 text-[11px] font-semibold uppercase tracking-[0.12em] transition-colors",
                      disabled || block.fixed_time
                        ? "cursor-not-allowed border-[var(--planner-board-border)] text-[var(--planner-board-muted-strong)] opacity-60"
                        : "border-[var(--planner-board-border)] text-[var(--planner-board-muted-strong)] hover:bg-[var(--planner-board-soft)]",
                    )}
                  >
                    {plan.day_label}
                  </button>
                ))}
              <button
                type="button"
                disabled={disabled}
                onClick={() =>
                  onAction({
                    action_id: crypto.randomUUID(),
                    type: "send_activity_candidate_to_reserve",
                    activity_candidate_id: candidate.id,
                    activity_candidate_title: candidate.title,
                    activity_candidate_kind: candidate.kind,
                  })
                }
                className={cn(
                  "rounded-md border px-3 py-2 text-[11px] font-semibold uppercase tracking-[0.12em] transition-colors",
                  disabled
                    ? "cursor-wait border-[var(--planner-board-border)] text-[var(--planner-board-muted-strong)] opacity-70"
                    : "border-[var(--planner-board-border)] text-[var(--planner-board-muted-strong)] hover:bg-[var(--planner-board-soft)]",
                )}
              >
                Reserve
              </button>
            </div>
          ) : null}
        </div>
      </div>
    </article>
  );
}

function ActivityWorkspaceStat({
  label,
  value,
}: {
  label: string;
  value: number;
}) {
  return (
    <div className="rounded-xl border border-[var(--planner-board-border)] bg-[var(--planner-board-card)] px-5 py-4 shadow-[0_1px_1px_rgba(0,0,0,0.04),0_8px_18px_rgba(0,0,0,0.04)]">
      <p className="text-xs font-semibold uppercase tracking-[0.14em] text-[var(--planner-board-muted-strong)]">
        {label}
      </p>
      <p className="mt-2 font-display text-[1.8rem] font-bold leading-none text-[var(--planner-board-text)]">
        {value}
      </p>
    </div>
  );
}

function AdvancedActivityCandidateCardView({
  candidate,
  dayPlans,
  scheduledBlock,
  reserved = false,
  disabled,
  onAction,
}: {
  candidate: AdvancedActivityCandidateCard;
  dayPlans: NonNullable<TripSuggestionBoardState["activity_day_plans"]>;
  scheduledBlock: NonNullable<
    NonNullable<TripSuggestionBoardState["activity_day_plans"]>[number]["blocks"]
  >[number] | null;
  reserved?: boolean;
  disabled: boolean;
  onAction: (action: PlannerBoardActionIntent) => void;
}) {
  const kindLabel = candidate.kind === "event" ? "Event" : "Activity";
  const dispositionLabel =
    candidate.disposition === "essential"
      ? "Leading pick"
      : candidate.disposition === "maybe"
        ? "In the mix"
        : "Left out";
  const timingLabel = candidate.start_at
    ? new Date(candidate.start_at).toLocaleString(undefined, {
        month: "short",
        day: "numeric",
        hour: "numeric",
        minute: "2-digit",
      })
    : null;
  const scheduleLabel = scheduledBlock
    ? `${scheduledBlock.day_label}${scheduledBlock.daypart ? ` • ${formatDaypartLabel(scheduledBlock.daypart)}` : ""}`
    : reserved
      ? "Saved in reserve"
      : null;
  const fixedTimeLocked = candidate.kind === "event" && Boolean(candidate.start_at);

  return (
    <article className="rounded-xl border border-[var(--planner-board-border)] bg-[var(--planner-board-card)] px-5 py-5 shadow-[0_1px_1px_rgba(0,0,0,0.04),0_8px_18px_rgba(0,0,0,0.04)]">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-2">
            <span className="rounded-md bg-[var(--planner-board-soft)] px-2.5 py-1 text-[10px] font-semibold uppercase tracking-[0.14em] text-[var(--planner-board-muted-strong)]">
              {kindLabel}
            </span>
            {candidate.recommended ? (
              <span className="rounded-md bg-[color:color-mix(in_srgb,var(--accent)_10%,transparent)] px-2.5 py-1 text-[10px] font-semibold uppercase tracking-[0.14em] text-[color:var(--accent)]">
                Recommended
              </span>
            ) : null}
            <span className="rounded-md border border-[var(--planner-board-border)] px-2.5 py-1 text-[10px] font-semibold uppercase tracking-[0.14em] text-[var(--planner-board-muted-strong)]">
              {dispositionLabel}
            </span>
            {scheduleLabel ? (
              <span className="rounded-md border border-[color:var(--accent)] px-2.5 py-1 text-[10px] font-semibold uppercase tracking-[0.14em] text-[color:var(--accent)]">
                {scheduleLabel}
              </span>
            ) : null}
          </div>

          <h3 className="mt-3 font-display text-xl font-bold tracking-[-0.02em] text-[var(--planner-board-text)]">
            {candidate.title}
          </h3>

          {candidate.kind === "event" && candidate.venue_name ? (
            <p className="mt-2 text-sm font-medium text-[var(--planner-board-muted-strong)]">
              {candidate.venue_name}
            </p>
          ) : null}

          <div className="mt-3 flex flex-wrap gap-3 text-sm text-[var(--planner-board-muted)]">
            {candidate.location_label ? (
              <span className="inline-flex items-center gap-1.5">
                <MapPin className="h-4 w-4" />
                {candidate.location_label}
              </span>
            ) : null}
            {timingLabel ? (
              <span className="inline-flex items-center gap-1.5">
                <CalendarRange className="h-4 w-4" />
                {timingLabel}
              </span>
            ) : null}
          </div>

          {candidate.summary ? (
            <p className="mt-3 text-sm leading-7 text-[var(--planner-board-muted)]">
              {candidate.summary}
            </p>
          ) : null}

          {fixedTimeLocked ? (
            <p className="mt-3 text-sm leading-6 text-[var(--planner-board-muted)]">
              This event already has a fixed time, so the planner can keep it or
              send it to reserve, but it will not silently rewrite the slot.
            </p>
          ) : null}

          {(candidate.status_text ||
            candidate.price_text ||
            candidate.availability_text) ? (
            <div className="mt-4 flex flex-wrap gap-2">
              {[candidate.status_text, candidate.price_text, candidate.availability_text]
                .filter(Boolean)
                .map((detail) => (
                  <span
                    key={detail}
                    className="rounded-md bg-[var(--planner-board-soft)] px-3 py-1.5 text-xs font-medium text-[var(--planner-board-muted)]"
                  >
                    {detail}
                  </span>
                ))}
            </div>
          ) : null}

          {candidate.ranking_reasons.length ? (
            <div className="mt-4 flex flex-wrap gap-2">
              {candidate.ranking_reasons.map((reason) => (
                <span
                  key={reason}
                  className="rounded-md bg-[var(--planner-board-soft)] px-3 py-1.5 text-xs font-medium text-[var(--planner-board-muted)]"
                >
                  {reason}
                </span>
              ))}
            </div>
          ) : null}

          {candidate.kind === "event" && candidate.source_url ? (
            <a
              href={candidate.source_url}
              target="_blank"
              rel="noreferrer"
              className="mt-4 inline-flex items-center gap-1.5 text-sm font-semibold text-[color:var(--accent)] hover:underline"
            >
              Open event listing
              <ExternalLink className="h-4 w-4" />
            </a>
          ) : null}
        </div>

        <div className="flex shrink-0 flex-wrap gap-2">
          {(["essential", "maybe", "pass"] as const).map((disposition) => (
            <button
              key={disposition}
              type="button"
              disabled={disabled}
              onClick={() =>
                onAction({
                  action_id: crypto.randomUUID(),
                  type: "set_activity_candidate_disposition",
                  activity_candidate_id: candidate.id,
                  activity_candidate_title: candidate.title,
                  activity_candidate_kind: candidate.kind,
                  activity_candidate_disposition: disposition,
                })
              }
              className={cn(
                "rounded-md border px-3 py-2 text-xs font-semibold uppercase tracking-[0.12em] transition-colors",
                candidate.disposition === disposition
                  ? "border-[color:var(--accent)] bg-[color:color-mix(in_srgb,var(--accent)_10%,transparent)] text-[color:var(--accent)]"
                  : "border-[var(--planner-board-border)] text-[var(--planner-board-muted-strong)] hover:bg-[var(--planner-board-soft)]",
                disabled ? "cursor-wait opacity-70" : "",
              )}
            >
              {disposition === "essential"
                ? "Shape trip"
                : disposition === "maybe"
                  ? "Keep option"
                  : "Skip"}
            </button>
          ))}
        </div>
      </div>

      {candidate.disposition !== "pass" ? (
        <div className="mt-5 space-y-4 border-t border-[var(--planner-board-border)] pt-4">
          <div className="flex flex-wrap gap-2">
            <button
              type="button"
              disabled={disabled}
              onClick={() =>
                onAction({
                  action_id: crypto.randomUUID(),
                  type: reserved
                    ? "restore_activity_candidate_from_reserve"
                    : "send_activity_candidate_to_reserve",
                  activity_candidate_id: candidate.id,
                  activity_candidate_title: candidate.title,
                  activity_candidate_kind: candidate.kind,
                })
              }
              className={cn(
                "rounded-md border px-3 py-2 text-[11px] font-semibold uppercase tracking-[0.12em] transition-colors",
                disabled
                  ? "cursor-wait border-[var(--planner-board-border)] text-[var(--planner-board-muted-strong)] opacity-70"
                  : "border-[var(--planner-board-border)] text-[var(--planner-board-muted-strong)] hover:bg-[var(--planner-board-soft)]",
              )}
            >
              {reserved ? "Restore" : "Save for later"}
            </button>
            {!fixedTimeLocked && scheduledBlock ? (
              <>
                <button
                  type="button"
                  disabled={disabled}
                  onClick={() =>
                    onAction({
                      action_id: crypto.randomUUID(),
                      type: "move_activity_candidate_earlier",
                      activity_candidate_id: candidate.id,
                      activity_candidate_title: candidate.title,
                      activity_candidate_kind: candidate.kind,
                    })
                  }
                  className={cn(
                    "rounded-md border px-3 py-2 text-[11px] font-semibold uppercase tracking-[0.12em] transition-colors",
                    disabled
                      ? "cursor-wait border-[var(--planner-board-border)] text-[var(--planner-board-muted-strong)] opacity-70"
                      : "border-[var(--planner-board-border)] text-[var(--planner-board-muted-strong)] hover:bg-[var(--planner-board-soft)]",
                  )}
                >
                  Earlier
                </button>
                <button
                  type="button"
                  disabled={disabled}
                  onClick={() =>
                    onAction({
                      action_id: crypto.randomUUID(),
                      type: "move_activity_candidate_later",
                      activity_candidate_id: candidate.id,
                      activity_candidate_title: candidate.title,
                      activity_candidate_kind: candidate.kind,
                    })
                  }
                  className={cn(
                    "rounded-md border px-3 py-2 text-[11px] font-semibold uppercase tracking-[0.12em] transition-colors",
                    disabled
                      ? "cursor-wait border-[var(--planner-board-border)] text-[var(--planner-board-muted-strong)] opacity-70"
                      : "border-[var(--planner-board-border)] text-[var(--planner-board-muted-strong)] hover:bg-[var(--planner-board-soft)]",
                  )}
                >
                  Later
                </button>
              </>
            ) : null}
          </div>

          {!fixedTimeLocked ? (
            <>
              <div className="space-y-2">
                <p className="text-[11px] font-semibold uppercase tracking-[0.14em] text-[var(--planner-board-muted-strong)]">
                  Place on a day
                </p>
                <div className="flex flex-wrap gap-2">
                  {dayPlans.map((dayPlan) => (
                    <button
                      key={dayPlan.id}
                      type="button"
                      disabled={disabled}
                      onClick={() =>
                        onAction({
                          action_id: crypto.randomUUID(),
                          type: "move_activity_candidate_to_day",
                          activity_candidate_id: candidate.id,
                          activity_candidate_title: candidate.title,
                          activity_candidate_kind: candidate.kind,
                          activity_target_day_index: dayPlan.day_index,
                        })
                      }
                      className={cn(
                        "rounded-md border px-3 py-2 text-[11px] font-semibold uppercase tracking-[0.12em] transition-colors",
                        scheduledBlock?.day_index === dayPlan.day_index
                          ? "border-[color:var(--accent)] bg-[color:color-mix(in_srgb,var(--accent)_10%,transparent)] text-[color:var(--accent)]"
                          : disabled
                            ? "cursor-wait border-[var(--planner-board-border)] text-[var(--planner-board-muted-strong)] opacity-70"
                            : "border-[var(--planner-board-border)] text-[var(--planner-board-muted-strong)] hover:bg-[var(--planner-board-soft)]",
                      )}
                    >
                      {dayPlan.day_label}
                    </button>
                  ))}
                </div>
              </div>

              <div className="space-y-2">
                <p className="text-[11px] font-semibold uppercase tracking-[0.14em] text-[var(--planner-board-muted-strong)]">
                  Best part of the day
                </p>
                <div className="flex flex-wrap gap-2">
                  {(["morning", "afternoon", "evening"] as const).map((daypart) => (
                    <button
                      key={daypart}
                      type="button"
                      disabled={disabled}
                      onClick={() =>
                        onAction({
                          action_id: crypto.randomUUID(),
                          type: "pin_activity_candidate_daypart",
                          activity_candidate_id: candidate.id,
                          activity_candidate_title: candidate.title,
                          activity_candidate_kind: candidate.kind,
                          activity_target_daypart: daypart,
                        })
                      }
                      className={cn(
                        "rounded-md border px-3 py-2 text-[11px] font-semibold uppercase tracking-[0.12em] transition-colors",
                        scheduledBlock?.daypart === daypart
                          ? "border-[color:var(--accent)] bg-[color:color-mix(in_srgb,var(--accent)_10%,transparent)] text-[color:var(--accent)]"
                          : disabled
                            ? "cursor-wait border-[var(--planner-board-border)] text-[var(--planner-board-muted-strong)] opacity-70"
                            : "border-[var(--planner-board-border)] text-[var(--planner-board-muted-strong)] hover:bg-[var(--planner-board-soft)]",
                      )}
                    >
                      {formatDaypartLabel(daypart)}
                    </button>
                  ))}
                </div>
              </div>
            </>
          ) : null}
        </div>
      ) : null}
    </article>
  );
}

function formatDaypartLabel(daypart: PlannerActivityDaypart) {
  return daypart.charAt(0).toUpperCase() + daypart.slice(1);
}

function formatFlightResultsStatus(
  status: TripSuggestionBoardState["flight_results_status"],
) {
  return {
    blocked: "Needs details",
    ready: "Options ready",
    placeholder: "Working shapes",
  }[status ?? "blocked"];
}

function formatFlightDateTime(value: string | null | undefined) {
  if (!value) {
    return null;
  }
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return null;
  }
  return date.toLocaleString(undefined, {
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  });
}

function formatFlightStopLabel(value: number | null | undefined) {
  if (value == null) {
    return null;
  }
  if (value === 0) {
    return "Direct";
  }
  if (value === 1) {
    return "1 stop";
  }
  return `${value} stops`;
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
          {card.cta_label || "Choose this focus"}
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
  disabled,
  onAction,
}: {
  board: TripSuggestionBoardState;
  compact?: boolean;
  disabled: boolean;
  onAction: (action: PlannerBoardActionIntent) => void;
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

      {board.mode === "advanced_stay_review" ? (
        <div className={cn(compact ? "mt-3" : "mt-4")}>
          <button
            type="button"
            disabled={disabled}
            onClick={() =>
              onAction({
                action_id: crypto.randomUUID(),
                type: "keep_current_stay_choice",
              })
            }
            className={cn(
              "inline-flex items-center rounded-lg border px-4 py-2.5 text-sm font-semibold transition-colors",
              disabled
                ? "cursor-not-allowed border-[var(--planner-board-border)] bg-[var(--planner-board-soft)] text-[var(--planner-board-muted-strong)]"
                : "border-[var(--planner-board-border)] bg-[var(--planner-board-soft)] text-[var(--planner-board-text)] hover:bg-[color:color-mix(in_srgb,var(--planner-board-soft)_62%,white)]",
            )}
            >
            Keep this base anyway
          </button>
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
          {isReviewMode ? (
            <button
              type="button"
              disabled={disabled}
              onClick={() =>
                onAction({
                  action_id: crypto.randomUUID(),
                  type: "keep_current_hotel_choice",
                })
              }
              className={cn(
                "inline-flex items-center rounded-md border px-3.5 py-2 text-sm font-semibold transition-colors",
                disabled
                  ? "cursor-not-allowed border-[var(--planner-board-border)] bg-[var(--planner-board-soft)] text-[var(--planner-board-muted-strong)]"
                  : "border-[var(--planner-board-border)] bg-[var(--planner-board-soft)] text-[var(--planner-board-text)] hover:bg-[color:color-mix(in_srgb,var(--planner-board-soft)_62%,white)]",
              )}
            >
              Keep this hotel anyway
            </button>
          ) : null}
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

function formatTripDirectionPrimaryLabel(primary: PlannerTripDirectionPrimary) {
  return {
    food_led: "Food-led",
    culture_led: "Culture-led",
    nightlife_led: "Nightlife-led",
    outdoors_led: "Outdoors-led",
    balanced: "Balanced",
  }[primary];
}

function tripDirectionPrimaryDescription(primary: PlannerTripDirectionPrimary) {
  return {
    food_led:
      "Let markets, tastings, dining neighborhoods, and culinary moments lead the trip shape.",
    culture_led:
      "Let museums, temples, galleries, heritage walks, and performances lead the trip shape.",
    nightlife_led:
      "Let evening districts, bars, late events, and live music pull the trip later into the day.",
    outdoors_led:
      "Let parks, viewpoints, open-air routes, hikes, and day trips lead the trip shape.",
    balanced:
      "Keep the trip broad and mixed, with no one kind of experience dominating too early.",
  }[primary];
}

function formatTripDirectionAccentLabel(accent: PlannerTripDirectionAccent) {
  return {
    local: "Local",
    classic: "Classic",
    polished: "Polished",
    romantic: "Romantic",
    relaxed: "Relaxed",
  }[accent];
}

function tripDirectionAccentDescription(accent: PlannerTripDirectionAccent) {
  return {
    local:
      "Favor neighborhood-scale picks and experiences that feel closer to everyday city rhythm.",
    classic:
      "Keep first-time icons and signature anchors visible early in the shortlist.",
    polished:
      "Favor refined, design-forward, and reservation-worthy moments when choices are close.",
    romantic:
      "Favor scenic, intimate, and couple-friendly moments without changing the main direction.",
    relaxed:
      "Keep the shortlist a little lighter and easier, with less friction in how days are shaped.",
  }[accent];
}

function formatTripPaceLabel(pace: PlannerTripPace) {
  return {
    slow: "Slow",
    balanced: "Balanced",
    full: "Full",
  }[pace];
}

function tripPaceDescription(pace: PlannerTripPace) {
  return {
    slow: "Fewer anchors, more open time, and lower-friction days.",
    balanced: "Two main moments most days, with flexible room around them.",
    full: "Denser days, more coverage, and more willingness to use all dayparts.",
  }[pace];
}

function formatTripTradeoffAxisLabel(axis: PlannerTripStyleTradeoffAxis) {
  return {
    must_sees_vs_wandering: "Must-sees vs wandering",
    convenience_vs_atmosphere: "Convenience vs atmosphere",
    early_starts_vs_evening_energy: "Early starts vs evening energy",
    polished_vs_hidden_gems: "Polished vs hidden gems",
  }[axis];
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

function formatReviewStatus(status: string | null | undefined) {
  if (status === "needs_review") {
    return "Worth reviewing";
  }
  if (status === "ready") {
    return "Selected";
  }
  return "Flexible";
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
