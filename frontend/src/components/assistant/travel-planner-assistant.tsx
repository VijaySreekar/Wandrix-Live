"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import {
  ArrowUp,
  Bot,
  Sparkles,
  UserRound,
} from "lucide-react";

import {
  AssistantRuntimeProvider,
  ComposerPrimitive,
  MessagePrimitive,
  ThreadPrimitive,
  useThread,
  useLocalRuntime,
  type ChatModelAdapter,
} from "@assistant-ui/react";

import { TravelPlannerBoardActions } from "@/components/assistant/travel-planner-board-actions";
import {
  getTripConversationHistory,
  sendTripConversationMessage,
} from "@/lib/api/conversation";
import {
  normalizeHistoryMessages,
  readCachedThreadMessages,
  writeCachedThreadMessages,
  type PersistedThreadMessage,
} from "@/lib/chat-history-cache";
import { resolvePlannerLocationForTurn } from "@/lib/planner-location";
import type { BrowserAuthSnapshot } from "@/lib/supabase/auth-snapshot";
import type { ConversationBoardAction, PlannerProfileContext } from "@/types/conversation";
import type { PlannerBoardActionIntent } from "@/types/planner-board";
import type { PlannerWorkspaceState } from "@/types/planner-workspace";
import type { TripDraft } from "@/types/trip-draft";

type TravelPlannerAssistantProps = {
  activeTripId: string | null;
  authSnapshot: BrowserAuthSnapshot | null;
  skipInitialHistorySync: boolean;
  onEnsurePersistedTrip: () => Promise<PlannerWorkspaceState | null>;
  onActivatePersistedTrip: (workspace: PlannerWorkspaceState) => void;
  workspace: PlannerWorkspaceState | null;
  isBootstrapping: boolean;
  workspaceError: string | null;
  pendingBoardAction: PlannerBoardActionIntent | null;
  onBoardActionHandled: (actionId: string) => void;
  onDraftUpdated: (tripDraft: TripDraft) => void;
};

export function TravelPlannerAssistant({
  activeTripId,
  authSnapshot,
  skipInitialHistorySync,
  onEnsurePersistedTrip,
  onActivatePersistedTrip,
  workspace,
  isBootstrapping,
  workspaceError,
  pendingBoardAction,
  onBoardActionHandled,
  onDraftUpdated,
}: TravelPlannerAssistantProps) {
  const [profileContext, setProfileContext] = useState<PlannerProfileContext | null>(
    null,
  );
  const [savedThreadState, setSavedThreadState] = useState<{
    tripId: string | null;
    messages: PersistedThreadMessage[] | null;
  }>({
    tripId: null,
    messages: null,
  });
  const [isSyncingHistory, setIsSyncingHistory] = useState(false);
  const boardActionRef = useRef<ConversationBoardAction | null>(null);

  const tripId = activeTripId ?? workspace?.trip.trip_id ?? null;
  const hasActiveWorkspace = Boolean(
    tripId && workspace && workspace.trip.trip_id === tripId,
  );
  const savedMessages =
    savedThreadState.tripId === tripId ? savedThreadState.messages : null;

  useEffect(() => {
    let cancelled = false;

    async function loadSavedMessages() {
      if (!tripId) {
        setSavedThreadState({
          tripId: null,
          messages: [],
        });
        setIsSyncingHistory(false);
        return;
      }

      const cachedMessages = readCachedThreadMessages(tripId);
      setSavedThreadState({
        tripId,
        messages: cachedMessages,
      });
      if (skipInitialHistorySync) {
        setIsSyncingHistory(false);
        return;
      }

      setIsSyncingHistory(true);

      try {
        if (authSnapshot?.accessToken) {
          const history = await getTripConversationHistory(
            tripId,
            authSnapshot.accessToken,
          );

          if (history.messages.length > 0) {
            const normalizedMessages = normalizeHistoryMessages(history.messages);

            if (!cancelled) {
              setSavedThreadState({
                tripId,
                messages: normalizedMessages,
              });
              writeCachedThreadMessages(tripId, normalizedMessages);
            }
            return;
          }

          if (!cancelled) {
            setSavedThreadState({
              tripId,
              messages: [],
            });
            writeCachedThreadMessages(tripId, []);
          }
        }
      } catch {
        if (!cancelled && cachedMessages.length === 0) {
          setSavedThreadState({
            tripId,
            messages: [],
          });
        }
      } finally {
        if (!cancelled) {
          setIsSyncingHistory(false);
        }
      }
    }

    void loadSavedMessages();

    return () => {
      cancelled = true;
    };
  }, [authSnapshot?.accessToken, skipInitialHistorySync, tripId]);

  useEffect(() => {
    let cancelled = false;

    async function loadProfileContext() {
      const userId = authSnapshot?.userId ?? null;
      const userMetadata = authSnapshot?.userMetadata ?? {};

      if (!userId) {
        if (!cancelled) {
          setProfileContext(null);
        }
        return;
      }

      const storageKey = `wandrix:profile-defaults:${userId}`;

      try {
        const stored = window.localStorage.getItem(storageKey);
        const parsed = stored ? (JSON.parse(stored) as Record<string, unknown>) : {};

        if (!cancelled) {
          setProfileContext({
            display_name:
              typeof parsed.displayName === "string"
                ? parsed.displayName
                : typeof userMetadata.full_name === "string"
                  ? userMetadata.full_name
                  : typeof userMetadata.name === "string"
                    ? userMetadata.name
                    : null,
            first_name:
              typeof parsed.firstName === "string" ? parsed.firstName : null,
            home_airport:
              typeof parsed.homeAirport === "string" ? parsed.homeAirport : null,
            preferred_currency:
              typeof parsed.preferredCurrency === "string"
                ? parsed.preferredCurrency
                : null,
            home_city: typeof parsed.homeCity === "string" ? parsed.homeCity : null,
            home_country:
              typeof parsed.homeCountry === "string" ? parsed.homeCountry : null,
            trip_pace: typeof parsed.tripPace === "string" ? parsed.tripPace : null,
            preferred_styles: Array.isArray(parsed.preferredStyles)
              ? parsed.preferredStyles.filter(
                  (value): value is string => typeof value === "string",
                )
              : [],
            location_summary:
              typeof parsed.locationSummary === "string"
                ? parsed.locationSummary
                : null,
            location_assist_enabled:
              typeof parsed.locationAssistEnabled === "boolean"
                ? parsed.locationAssistEnabled
                : null,
          });
        }
      } catch {
        if (!cancelled) {
          setProfileContext(null);
        }
      }
    }

    void loadProfileContext();

    return () => {
      cancelled = true;
    };
  }, [authSnapshot?.userId, authSnapshot?.userMetadata]);

  const adapter = useMemo<ChatModelAdapter>(
    () => ({
      async *run({ messages, abortSignal }) {
        const latestMessage = messages.at(-1);
        const latestText =
          latestMessage?.content
            .filter((part) => part.type === "text")
            .map((part) => part.text)
            .join(" ")
            .trim() ?? "";

        const response = await buildAssistantReply({
          activeTripId: tripId,
          isBootstrapping,
          workspace,
          workspaceError,
          latestText,
          authSnapshot,
          onEnsurePersistedTrip,
          onActivatePersistedTrip,
          profileContext,
          pendingBoardAction: boardActionRef.current,
          onDraftUpdated,
        });

        boardActionRef.current = null;

        let cumulativeText = "";

        for (const chunk of chunkResponse(response)) {
          if (abortSignal.aborted) {
            return;
          }

          cumulativeText = cumulativeText ? `${cumulativeText} ${chunk}` : chunk;

          yield {
            content: [{ type: "text", text: cumulativeText }],
          };

          await sleep(120, abortSignal);
        }
      },
    }),
    [
      authSnapshot,
      isBootstrapping,
      onActivatePersistedTrip,
      onEnsurePersistedTrip,
      onDraftUpdated,
      profileContext,
      boardActionRef,
      tripId,
      workspace,
      workspaceError,
    ],
  );

  if (tripId && savedMessages === null) {
    return (
      <section className="relative flex h-full min-h-0 flex-col bg-[color:var(--chat-pane-bg)]">
        <div className="flex min-h-0 flex-1 items-center justify-center px-8">
          <div className="max-w-md text-center">
            <p className="text-sm font-medium text-foreground">
              Restoring this trip conversation
            </p>
            <p className="mt-2 text-sm leading-7 text-muted-foreground">
              Pulling the most recent local thread state back into the workspace so
              the chat and live board feel connected again.
            </p>
          </div>
        </div>
      </section>
    );
  }

  return (
    <TravelPlannerAssistantRuntime
      key={tripId ?? "wandrix-chat-empty"}
      adapter={adapter}
      tripId={tripId}
      initialMessages={savedMessages ?? []}
      isSyncingHistory={isSyncingHistory}
      profileContext={profileContext}
      isBootstrapping={isBootstrapping}
      hasWorkspace={hasActiveWorkspace}
      hasError={Boolean(workspaceError)}
      pendingBoardAction={pendingBoardAction}
      onBoardActionHandled={onBoardActionHandled}
      onBoardActionReadyForBackend={(action) => {
        boardActionRef.current = action;
      }}
      onDirectBoardActionSubmit={async (action) => {
        return await buildAssistantReply({
          activeTripId: tripId,
          isBootstrapping,
          workspace,
          workspaceError,
          latestText: " ",
          authSnapshot,
          onEnsurePersistedTrip,
          onActivatePersistedTrip,
          profileContext,
          pendingBoardAction: action,
          onDraftUpdated,
        });
      }}
    />
  );
}

function TravelPlannerAssistantRuntime({
  adapter,
  tripId,
  initialMessages,
  isSyncingHistory,
  profileContext,
  isBootstrapping,
  hasWorkspace,
  hasError,
  pendingBoardAction,
  onBoardActionHandled,
  onBoardActionReadyForBackend,
  onDirectBoardActionSubmit,
}: {
  adapter: ChatModelAdapter;
  tripId: string | null;
  initialMessages: PersistedThreadMessage[];
  isSyncingHistory: boolean;
  profileContext: PlannerProfileContext | null;
  isBootstrapping: boolean;
  hasWorkspace: boolean;
  hasError: boolean;
  pendingBoardAction: PlannerBoardActionIntent | null;
  onBoardActionHandled: (actionId: string) => void;
  onBoardActionReadyForBackend: (action: ConversationBoardAction) => void;
  onDirectBoardActionSubmit: (action: ConversationBoardAction) => Promise<string>;
}) {
  const runtime = useLocalRuntime(adapter, {
    initialMessages: initialMessages.map((message) => ({
      id: message.id,
      role: message.role,
      content: message.content,
      createdAt: message.createdAt ? new Date(message.createdAt) : undefined,
    })),
  });

  return (
    <AssistantRuntimeProvider runtime={runtime}>
      <PersistedThreadStateSync tripId={tripId} />
      <TravelPlannerBoardActions
        pendingBoardAction={pendingBoardAction}
        disabled={isBootstrapping || !hasWorkspace || hasError}
        onHandled={onBoardActionHandled}
        onActionReadyForBackend={onBoardActionReadyForBackend}
        onDirectActionSubmit={onDirectBoardActionSubmit}
      />
      <section className="relative flex h-full min-h-0 flex-col bg-[color:var(--chat-pane-bg)]">
        <ThreadPrimitive.Root className="flex min-h-0 flex-1 flex-col overflow-hidden">
        <ThreadPrimitive.Viewport className="chat-workspace-scroll flex min-h-0 flex-1 flex-col overflow-y-auto px-4 py-6 sm:px-8">
          {isSyncingHistory ? <ConversationSyncBanner /> : null}
            <ThreadPrimitive.Empty>
              <AssistantWelcome
                disabled={isBootstrapping}
                hasWorkspace={hasWorkspace}
                hasError={hasError}
                profileContext={profileContext}
              />
            </ThreadPrimitive.Empty>

            <div className="mx-auto mt-auto flex w-full max-w-[52rem] flex-col gap-6 pb-40">
              <ThreadPrimitive.Messages
                components={{
                  UserMessage,
                  AssistantMessage,
                }}
              />
            </div>
          </ThreadPrimitive.Viewport>

          <Composer
            disabled={isBootstrapping || !hasWorkspace || hasError}
            disabledPlaceholder={
              isBootstrapping
                ? "Attaching the planner workspace..."
                : !hasWorkspace
                  ? "Opening this trip..."
                  : "Resolve the workspace issue before sending."
            }
          />
        </ThreadPrimitive.Root>
      </section>
    </AssistantRuntimeProvider>
  );
}

function PersistedThreadStateSync({ tripId }: { tripId: string | null }) {
  const messages = useThread((state) => state.messages);

  useEffect(() => {
    if (!tripId) {
      return;
    }

    const persistedMessages = messages.flatMap((message) => {
      const textContent = message.content
        .filter((part) => part.type === "text")
        .map((part) => part.text)
        .join("\n")
        .trim();

      if (!textContent) {
        return [];
      }

      return [
        {
          id: message.id,
          role: message.role,
          content: textContent,
          createdAt:
            message.createdAt instanceof Date
              ? message.createdAt.toISOString()
              : undefined,
        } satisfies PersistedThreadMessage,
      ];
    });

    writeCachedThreadMessages(tripId, persistedMessages);
  }, [messages, tripId]);

  return null;
}

function ConversationSyncBanner() {
  return (
    <div className="mx-auto mb-5 flex w-full max-w-[52rem] items-center justify-center">
      <div className="inline-flex items-center gap-2 rounded-full border border-border/60 bg-background/88 px-3 py-1.5 text-[0.72rem] text-muted-foreground shadow-[var(--chat-shadow-soft)]">
        <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-[color:var(--accent)]" />
        <span>Syncing this conversation in the background.</span>
      </div>
    </div>
  );
}

function AssistantWelcome({
  disabled,
  hasWorkspace,
  hasError,
  profileContext,
}: {
  disabled: boolean;
  hasWorkspace: boolean;
  hasError: boolean;
  profileContext: PlannerProfileContext | null;
}) {
  const greetingName =
    profileContext?.first_name ||
    profileContext?.display_name?.split(" ")[0] ||
    "there";
  const contextLine = buildWelcomeContextLine(profileContext);

  return (
    <div className="mx-auto flex h-full min-h-[24rem] w-full max-w-[52rem] flex-col justify-end gap-6 px-1 pt-2">
      <div className="space-y-2">
        <div className="text-xs font-medium uppercase tracking-[0.22em] text-[color:var(--accent)]">
          Wandrix planner
        </div>
        <div className="space-y-2">
          <div className="text-sm font-semibold text-foreground">
            {`Hey ${greetingName}, I’m Wandrix.`}
          </div>
          <p className="max-w-2xl text-sm text-muted-foreground">
            {contextLine}
          </p>
        </div>
        {disabled ? (
          <p className="text-sm text-muted-foreground">
            Finishing workspace setup before the first run.
          </p>
        ) : null}
        {!disabled && !hasWorkspace && !hasError ? (
          <p className="text-sm text-muted-foreground">
            Sign in first so the assistant can attach the conversation to a trip.
          </p>
        ) : null}
        {!disabled && hasError ? (
          <p className="text-sm text-muted-foreground">
            The workspace needs attention before the assistant can fully attach to it.
          </p>
        ) : null}
      </div>

      <div className="grid gap-3 sm:grid-cols-2">
        <ThreadPrimitive.Suggestion
          className="group rounded-xl border border-[color:var(--chat-rail-border)] bg-[color:var(--chat-rail-surface)] px-4 py-4 text-left transition-colors hover:border-[color:var(--chat-rail-border-strong)] hover:bg-[color:var(--chat-rail-surface-strong)] disabled:cursor-not-allowed disabled:opacity-60"
          prompt={
            profileContext?.home_airport
              ? `Plan a 5-day food and culture trip to Kyoto from ${profileContext.home_airport} for two adults.`
              : "Plan a 5-day food and culture trip to Kyoto for two adults."
          }
          autoSend
          disabled={disabled || !hasWorkspace}
        >
          <div className="flex items-start justify-between gap-3">
            <span className="inline-flex h-9 w-9 items-center justify-center rounded-lg border border-[color:var(--chat-rail-border)] bg-[color:var(--chat-rail-control-bg)] text-[color:var(--accent)]">
              <Sparkles className="h-4 w-4" />
            </span>
            <ArrowUp className="mt-0.5 h-4 w-4 rotate-45 text-muted-foreground transition-colors group-hover:text-foreground" />
          </div>
          <div className="mt-4 text-base font-semibold text-foreground">
            Kyoto food and culture
          </div>
          <div className="mt-1 text-sm leading-6 text-muted-foreground">
            {profileContext?.home_airport
              ? `Plan a 5-day food and culture trip to Kyoto from ${profileContext.home_airport} for two adults.`
              : "Plan a 5-day food and culture trip to Kyoto for two adults."}
          </div>
        </ThreadPrimitive.Suggestion>
        <ThreadPrimitive.Suggestion
          className="group rounded-xl border border-[color:var(--chat-rail-border)] bg-[color:var(--chat-rail-surface)] px-4 py-4 text-left transition-colors hover:border-[color:var(--chat-rail-border-strong)] hover:bg-[color:var(--chat-rail-surface-strong)] disabled:cursor-not-allowed disabled:opacity-60"
          prompt={
            profileContext?.preferred_currency
              ? `Help me shape a luxury long weekend in Lisbon with flights and hotel ideas, and keep the budget in ${profileContext.preferred_currency}.`
              : "Help me shape a luxury long weekend in Lisbon with flights and hotel ideas."
          }
          autoSend
          disabled={disabled || !hasWorkspace}
        >
          <div className="flex items-start justify-between gap-3">
            <span className="inline-flex h-9 w-9 items-center justify-center rounded-lg border border-[color:var(--chat-rail-border)] bg-[color:var(--chat-rail-control-bg)] text-[color:var(--accent)]">
              <Sparkles className="h-4 w-4" />
            </span>
            <ArrowUp className="mt-0.5 h-4 w-4 rotate-45 text-muted-foreground transition-colors group-hover:text-foreground" />
          </div>
          <div className="mt-4 text-base font-semibold text-foreground">
            Lisbon luxury weekend
          </div>
          <div className="mt-1 text-sm leading-6 text-muted-foreground">
            {profileContext?.preferred_currency
              ? `Help me shape a luxury long weekend in Lisbon with flights and hotel ideas, and keep the budget in ${profileContext.preferred_currency}.`
              : "Help me shape a luxury long weekend in Lisbon with flights and hotel ideas."}
          </div>
        </ThreadPrimitive.Suggestion>
        <ThreadPrimitive.Suggestion
          className="group rounded-xl border border-[color:var(--chat-rail-border)] bg-[color:var(--chat-rail-surface)] px-4 py-4 text-left transition-colors hover:border-[color:var(--chat-rail-border-strong)] hover:bg-[color:var(--chat-rail-surface-strong)] disabled:cursor-not-allowed disabled:opacity-60"
          prompt="Suggest a relaxed family trip to Barcelona with weather-aware activities."
          autoSend
          disabled={disabled || !hasWorkspace}
        >
          <div className="flex items-start justify-between gap-3">
            <span className="inline-flex h-9 w-9 items-center justify-center rounded-lg border border-[color:var(--chat-rail-border)] bg-[color:var(--chat-rail-control-bg)] text-[color:var(--accent)]">
              <Sparkles className="h-4 w-4" />
            </span>
            <ArrowUp className="mt-0.5 h-4 w-4 rotate-45 text-muted-foreground transition-colors group-hover:text-foreground" />
          </div>
          <div className="mt-4 text-base font-semibold text-foreground">
            Barcelona family escape
          </div>
          <div className="mt-1 text-sm leading-6 text-muted-foreground">
            Suggest a relaxed family trip to Barcelona with weather-aware activities.
          </div>
        </ThreadPrimitive.Suggestion>
        <ThreadPrimitive.Suggestion
          className="group rounded-xl border border-[color:var(--chat-rail-border)] bg-[color:var(--chat-rail-surface)] px-4 py-4 text-left transition-colors hover:border-[color:var(--chat-rail-border-strong)] hover:bg-[color:var(--chat-rail-surface-strong)] disabled:cursor-not-allowed disabled:opacity-60"
          prompt="What should the live trip board show as I refine my itinerary?"
          autoSend
          disabled={disabled}
        >
          <div className="flex items-start justify-between gap-3">
            <span className="inline-flex h-9 w-9 items-center justify-center rounded-lg border border-[color:var(--chat-rail-border)] bg-[color:var(--chat-rail-control-bg)] text-[color:var(--accent)]">
              <Sparkles className="h-4 w-4" />
            </span>
            <ArrowUp className="mt-0.5 h-4 w-4 rotate-45 text-muted-foreground transition-colors group-hover:text-foreground" />
          </div>
          <div className="mt-4 text-base font-semibold text-foreground">
            Live board guidance
          </div>
          <div className="mt-1 text-sm leading-6 text-muted-foreground">
            What should the live trip board show as I refine my itinerary?
          </div>
        </ThreadPrimitive.Suggestion>
      </div>
    </div>
  );
}

function UserMessage() {
  return (
    <MessagePrimitive.Root className="flex justify-end">
      <div className="flex max-w-[min(86%,44rem)] items-end gap-3">
        <div className="min-w-0 flex-1 rounded-[1.1rem] rounded-br-md border border-[color:color-mix(in_srgb,var(--accent)_24%,transparent)] bg-[color:color-mix(in_srgb,var(--accent)_10%,var(--color-background))] px-5 py-4 text-[length:var(--chat-size-body)] leading-[var(--chat-line-body)] text-foreground shadow-[var(--chat-shadow-card)]">
          <MessagePrimitive.Parts />
        </div>
        <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-muted/50 text-muted-foreground ring-1 ring-border/60">
          <UserRound className="h-4 w-4" />
        </div>
      </div>
    </MessagePrimitive.Root>
  );
}

function AssistantMessage() {
  return (
    <MessagePrimitive.Root className="flex flex-col items-start gap-3">
      <div className="flex items-start gap-3">
        <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-[color:color-mix(in_srgb,var(--accent)_12%,transparent)] text-[color:var(--accent)] shadow-[var(--chat-shadow-card)] ring-1 ring-[color:color-mix(in_srgb,var(--accent)_14%,transparent)]">
          <Bot className="h-4 w-4" />
        </div>
        <div className="max-w-[min(100%,48rem)]">
          <div className="overflow-hidden rounded-[1rem] border border-border/70 bg-background/92 shadow-[var(--chat-shadow-soft)] dark:bg-card/96">
            <div className="px-5 py-4 text-[length:var(--chat-size-body)] leading-[var(--chat-line-body)] text-foreground">
              <MessagePrimitive.Parts />
            </div>
          </div>
        </div>
      </div>
    </MessagePrimitive.Root>
  );
}

function Composer({
  disabled,
  disabledPlaceholder,
}: {
  disabled: boolean;
  disabledPlaceholder: string;
}) {
  const isRunning = useThread((state) => state.isRunning);

  return (
    <ComposerPrimitive.Root className="border-t border-[color:var(--chat-rail-border)] bg-[color:var(--chat-pane-bg)] px-4 pb-4 pt-3 sm:px-8">
      <div className="mx-auto w-full max-w-[52rem]">
        <div className="overflow-hidden rounded-xl border border-[color:var(--chat-rail-border-strong)] bg-[color:var(--chat-rail-surface-strong)] p-2">
          {isRunning ? (
            <div className="flex items-center gap-2 px-2 pb-2 text-xs text-muted-foreground">
              <span className="h-2 w-2 animate-pulse rounded-full bg-[color:var(--accent)]" />
              <span>Wandrix is thinking through the next planning step...</span>
            </div>
          ) : null}
          <div className="flex items-end gap-2">
            <div className="flex min-w-0 flex-1 rounded-lg border border-[color:var(--chat-rail-border)] bg-[color:var(--chat-rail-control-bg)] px-3 py-2.5 transition-colors focus-within:border-[color:var(--accent)]/45">
              <ComposerPrimitive.Input
                rows={1}
                placeholder={
                  disabled ? disabledPlaceholder : "Continue planning your trip..."
                }
                disabled={disabled}
                className="min-h-12 max-h-40 w-full resize-none bg-transparent px-1 py-0.5 text-sm leading-7 text-foreground outline-none placeholder:text-muted-foreground disabled:cursor-not-allowed disabled:text-muted-foreground"
              />
            </div>
            <ComposerPrimitive.Send asChild>
              <button
                type="button"
                disabled={disabled}
                className="flex h-12 w-12 shrink-0 items-center justify-center rounded-lg border border-[color:var(--chat-rail-border)] bg-[linear-gradient(135deg,var(--accent),var(--accent2))] text-white transition-opacity hover:opacity-95 disabled:cursor-not-allowed disabled:opacity-55"
                aria-label="Send message"
              >
                <ArrowUp className="h-4 w-4" />
              </button>
            </ComposerPrimitive.Send>
            <ComposerPrimitive.Cancel asChild>
              <button
                type="button"
                className="h-12 w-12 shrink-0 items-center justify-center rounded-lg border border-[color:var(--chat-rail-border)] bg-[color:var(--chat-rail-control-bg)] text-foreground transition-colors hover:bg-[color:var(--chat-rail-surface)] disabled:hidden"
                aria-label="Stop generating"
              >
                <span className="h-4 w-4 rounded-[0.2rem] bg-current" />
              </button>
            </ComposerPrimitive.Cancel>
          </div>
        </div>
      </div>
    </ComposerPrimitive.Root>
  );
}

function chunkResponse(text: string) {
  const sentences = text
    .split(/(?<=[.!?])\s+/)
    .map((sentence) => sentence.trim())
    .filter(Boolean);

  return sentences.length > 0 ? sentences : [text];
}

async function sleep(ms: number, signal: AbortSignal) {
  await new Promise<void>((resolve, reject) => {
    const timeout = window.setTimeout(resolve, ms);

    const onAbort = () => {
      window.clearTimeout(timeout);
      reject(new DOMException("Aborted", "AbortError"));
    };

    if (signal.aborted) {
      onAbort();
      return;
    }

    signal.addEventListener("abort", onAbort, { once: true });
  }).catch((error: unknown) => {
    if (error instanceof DOMException && error.name === "AbortError") {
      return;
    }

    throw error;
  });
}

async function buildAssistantReply({
  activeTripId,
  isBootstrapping,
  workspace,
  workspaceError,
  latestText,
  authSnapshot,
  onEnsurePersistedTrip,
  onActivatePersistedTrip,
  profileContext,
  pendingBoardAction,
  onDraftUpdated,
}: {
  activeTripId: string | null;
  isBootstrapping: boolean;
  workspace: PlannerWorkspaceState | null;
  workspaceError: string | null;
  latestText: string;
  authSnapshot: BrowserAuthSnapshot | null;
  onEnsurePersistedTrip: () => Promise<PlannerWorkspaceState | null>;
  onActivatePersistedTrip: (workspace: PlannerWorkspaceState) => void;
  profileContext: PlannerProfileContext | null;
  pendingBoardAction: ConversationBoardAction | null;
  onDraftUpdated: (tripDraft: TripDraft) => void;
}) {
  const hasAttachedWorkspace =
    Boolean(activeTripId) &&
    Boolean(workspace) &&
    workspace?.trip.trip_id === activeTripId;

  if (isBootstrapping || workspaceError || !hasAttachedWorkspace || !latestText) {
    return buildFallbackAssistantReply({
      activeTripId,
      isBootstrapping,
      workspace,
      workspaceError,
      latestText,
    });
  }

  if (!authSnapshot?.accessToken) {
    return "I can render the chat shell, but I could not read a valid Supabase access token for the backend conversation call.";
  }

  try {
    const persistedWorkspace =
      workspace?.isEphemeral ? await onEnsurePersistedTrip() : workspace;
    const resolvedTripId = persistedWorkspace?.trip.trip_id ?? activeTripId;

    if (!resolvedTripId) {
      return "I could not prepare a real trip yet, so I’m holding here until the workspace is ready.";
    }

    const currentLocationContext = await resolvePlannerLocationForTurn({
      tripId: resolvedTripId,
      profileContext,
      tripDraft: workspace?.tripDraft ?? null,
    });

    const response = await sendTripConversationMessage(
      resolvedTripId,
      {
        message: latestText,
        profile_context: profileContext ?? undefined,
        current_location_context: currentLocationContext ?? undefined,
        board_action: pendingBoardAction ?? undefined,
      },
      authSnapshot.accessToken,
    );

    if (workspace?.isEphemeral && persistedWorkspace) {
      const nowIso = new Date().toISOString();
      writeCachedThreadMessages(resolvedTripId, [
        {
          id: `${resolvedTripId}-user-0`,
          role: "user",
          content: latestText,
          createdAt: nowIso,
        },
        {
          id: `${resolvedTripId}-assistant-0`,
          role: "assistant",
          content: response.message,
          createdAt: nowIso,
        },
      ]);
      onActivatePersistedTrip({
        ...persistedWorkspace,
        trip: {
          ...persistedWorkspace.trip,
          title: response.trip_draft.title,
        },
        tripDraft: response.trip_draft,
      });
    }

    onDraftUpdated(response.trip_draft);

    return response.message;
  } catch (error) {
    return error instanceof Error
      ? error.message
      : "The backend conversation bridge failed unexpectedly.";
  }
}

function buildWelcomeContextLine(profileContext: PlannerProfileContext | null) {
  if (!profileContext) {
    return "Tell me where you want to go, roughly when, and how you want the trip to feel. I’ll shape it with you step by step without locking details too early.";
  }

  const contextBits = [
    profileContext.home_airport
      ? `starting from ${profileContext.home_airport}`
      : null,
    profileContext.preferred_currency
      ? `working in ${profileContext.preferred_currency}`
      : null,
    profileContext.home_city
      ? `using ${profileContext.home_city}${
          profileContext.home_country ? `, ${profileContext.home_country}` : ""
        } as your home base`
      : profileContext.home_country
        ? `using ${profileContext.home_country} as your home base`
        : null,
  ].filter(Boolean);

  if (contextBits.length === 0) {
    return "Tell me where you want to go, roughly when, and how you want the trip to feel. I’ll shape it with you step by step without locking details too early.";
  }

  return `I can start with ${contextBits.join(", ")} as soft defaults, but anything you say in chat will take priority for this trip. I’ll keep the early plan flexible until the core shape is clear.`;
}

function buildFallbackAssistantReply({
  activeTripId,
  isBootstrapping,
  workspace,
  workspaceError,
  latestText,
}: {
  activeTripId: string | null;
  isBootstrapping: boolean;
  workspace: PlannerWorkspaceState | null;
  workspaceError: string | null;
  latestText: string;
}) {
  if (isBootstrapping) {
    return "I’m just waiting for the trip workspace to finish booting before I attach this conversation properly.";
  }

  if (workspaceError) {
    return `I can talk here, but the trip workspace still needs fixing first: ${workspaceError}`;
  }

  if (!activeTripId) {
    return "I need a signed-in trip workspace before I can attach this conversation to a real trip and thread.";
  }

  if (!workspace || workspace.trip.trip_id !== activeTripId) {
    return "I have the conversation open, and I’m still attaching the trip workspace behind the scenes before I send the next planner turn.";
  }

  if (!latestText) {
    return `I’m attached to trip ${workspace.trip.trip_id}, and I’m ready when you are. Give me the destination, timing, or the kind of trip you want and I’ll start shaping it.`;
  }

  return `I'm routing your message to the backend trip conversation bridge for trip ${workspace.trip.trip_id}.`;
}
