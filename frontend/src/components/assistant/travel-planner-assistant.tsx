"use client";

import {
  useEffect,
  useMemo,
  useRef,
  useState,
  type CSSProperties,
  type ReactNode,
} from "react";
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
  useComposer,
  useComposerRuntime,
  useThread,
  useLocalRuntime,
  useMessage,
  useThreadRuntime,
  type ChatModelAdapter,
  type ThreadMessage,
} from "@assistant-ui/react";

import { TravelPlannerBoardActions } from "@/components/assistant/travel-planner-board-actions";
import { AgentThinkingTyping } from "@/components/assistant/agent-thinking-indicator";
import {
  getOpeningTurnResponse,
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
import { isEphemeralTripId } from "@/lib/trip-draft-starter";
import type { ConversationBoardAction, PlannerProfileContext } from "@/types/conversation";
import type { PlannerBoardActionIntent } from "@/types/planner-board";
import type { PlannerWorkspaceState } from "@/types/planner-workspace";
import type { TripDraft } from "@/types/trip-draft";

type TravelPlannerAssistantProps = {
  activeTripId: string | null;
  authSnapshot: BrowserAuthSnapshot | null;
  skipInitialHistorySync: boolean;
  isSwitchingTrips: boolean;
  requestedTripId: string | null;
  onEnsurePersistedTrip: (
    sourceTripId?: string | null,
  ) => Promise<PlannerWorkspaceState | null>;
  onActivatePersistedTrip: (
    workspace: PlannerWorkspaceState,
    sourceTripId?: string | null,
  ) => void;
  workspace: PlannerWorkspaceState | null;
  isBootstrapping: boolean;
  workspaceError: string | null;
  pendingBoardAction: PlannerBoardActionIntent | null;
  onBoardActionHandled: (actionId: string) => void;
  onDraftUpdated: (tripDraft: TripDraft) => void;
};

function buildThreadSeedMessages(messages: PersistedThreadMessage[]) {
  return messages.map((message) => ({
    id: message.id,
    role: message.role,
    content: message.content,
    createdAt: message.createdAt ? new Date(message.createdAt) : undefined,
  }));
}

function extractPersistedThreadMessages(
  messages: readonly ThreadMessage[],
): PersistedThreadMessage[] {
  return messages.flatMap((message) => {
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
}

function serializePersistedThreadMessages(messages: PersistedThreadMessage[]) {
  return JSON.stringify(
    messages.map((message) => ({
      ...message,
      createdAt: message.createdAt ?? null,
    })),
  );
}

function cacheAssistantTurn(
  tripId: string,
  userMessage: string,
  assistantMessage: string,
) {
  const nowIso = new Date().toISOString();
  const existingMessages = readCachedThreadMessages(tripId);
  const nextMessages = [
    ...existingMessages,
    {
      id: `${tripId}-user-${existingMessages.length}`,
      role: "user" as const,
      content: userMessage,
      createdAt: nowIso,
    },
    {
      id: `${tripId}-assistant-${existingMessages.length + 1}`,
      role: "assistant" as const,
      content: assistantMessage,
      createdAt: nowIso,
    },
  ];

  writeCachedThreadMessages(tripId, nextMessages);
}

function shouldActivatePersistedTrip(tripDraft: TripDraft) {
  const configuration = tripDraft.configuration;
  const hasStructuredTripSignal = Boolean(
    configuration.to_location ||
      configuration.from_location ||
      configuration.start_date ||
      configuration.end_date ||
      configuration.travel_window ||
      configuration.trip_length ||
      configuration.weather_preference ||
      configuration.budget_posture ||
      configuration.budget_amount ||
      configuration.budget_currency ||
      configuration.budget_gbp ||
      configuration.travelers.adults ||
      configuration.travelers.children ||
      configuration.travelers_flexible ||
      configuration.activity_styles.length > 0 ||
      configuration.custom_style,
  );
  const boardMode = tripDraft.conversation.suggestion_board.mode;

  return (
    tripDraft.status.phase !== "opening" ||
    hasStructuredTripSignal ||
    boardMode !== "helper" ||
    tripDraft.title.trim().toLowerCase() !== "trip planner"
  );
}

export function TravelPlannerAssistant({
  activeTripId,
  authSnapshot,
  skipInitialHistorySync,
  isSwitchingTrips,
  requestedTripId,
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

  const tripId = activeTripId ?? workspace?.trip.trip_id ?? null;
  const hasActiveWorkspace = Boolean(
    tripId && workspace && workspace.trip.trip_id === tripId,
  );
  const immediateCachedMessages = useMemo(
    () => (tripId ? readCachedThreadMessages(tripId) : []),
    [tripId],
  );
  const savedMessages =
    savedThreadState.tripId === tripId
      ? (savedThreadState.messages ?? immediateCachedMessages)
      : immediateCachedMessages;

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
            if (cachedMessages.length > 0) {
              setSavedThreadState({
                tripId,
                messages: cachedMessages,
              });
              return;
            }

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
          pendingBoardAction: null,
          onDraftUpdated,
        });

        if (abortSignal.aborted) {
          return;
        }

        yield {
          content: [{ type: "text", text: response }],
        };
      },
    }),
    [
      authSnapshot,
      isBootstrapping,
      onActivatePersistedTrip,
      onEnsurePersistedTrip,
      onDraftUpdated,
      profileContext,
      tripId,
      workspace,
      workspaceError,
    ],
  );

  return (
    <TravelPlannerAssistantRuntime
      adapter={adapter}
      tripId={tripId}
      initialMessages={savedMessages}
      isSyncingHistory={isSyncingHistory}
      isSwitchingTrips={isSwitchingTrips}
      profileContext={profileContext}
      isBootstrapping={isBootstrapping}
      hasWorkspace={hasActiveWorkspace}
      hasError={Boolean(workspaceError)}
      pendingBoardAction={pendingBoardAction}
      requestedTripId={requestedTripId}
      onBoardActionHandled={onBoardActionHandled}
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
  isSwitchingTrips,
  profileContext,
  isBootstrapping,
  hasWorkspace,
  hasError,
  pendingBoardAction,
  requestedTripId,
  onBoardActionHandled,
  onDirectBoardActionSubmit,
}: {
  adapter: ChatModelAdapter;
  tripId: string | null;
  initialMessages: PersistedThreadMessage[];
  isSyncingHistory: boolean;
  isSwitchingTrips: boolean;
  profileContext: PlannerProfileContext | null;
  isBootstrapping: boolean;
  hasWorkspace: boolean;
  hasError: boolean;
  pendingBoardAction: PlannerBoardActionIntent | null;
  requestedTripId: string | null;
  onBoardActionHandled: (actionId: string) => void;
  onDirectBoardActionSubmit: (action: ConversationBoardAction) => Promise<string>;
}) {
  const hydratedMessages = useMemo(
    () => buildThreadSeedMessages(initialMessages),
    [initialMessages],
  );
  const showInitialWorkspaceShell =
    isBootstrapping && !tripId && !hasWorkspace && !hasError;
  const hasHydratedMessages = hydratedMessages.length > 0;

  const runtime = useLocalRuntime(adapter, {
    initialMessages: hydratedMessages,
  });

  return (
    <AssistantRuntimeProvider runtime={runtime}>
      <ThreadHydrationSync
        tripId={tripId}
        initialMessages={initialMessages}
        hydratedMessages={hydratedMessages}
      />
      <PersistedThreadStateSync tripId={tripId} />
      <EmptyThreadViewportReset />
      <ChatViewportAutoScroll />
      <TravelPlannerBoardActions
        pendingBoardAction={pendingBoardAction}
        disabled={isBootstrapping || isSwitchingTrips || !hasWorkspace || hasError}
        onHandled={onBoardActionHandled}
        onDirectActionSubmit={onDirectBoardActionSubmit}
      />
      <section className="relative flex h-full min-h-0 flex-col bg-[color:var(--chat-pane-bg)]">
        <ThreadPrimitive.Root
          data-switching={isSwitchingTrips ? "true" : "false"}
          className="trip-switch-content flex min-h-0 flex-1 flex-col overflow-hidden"
        >
          <ThreadPrimitive.Viewport className="chat-workspace-scroll flex min-h-0 flex-1 flex-col overflow-y-auto px-4 py-6 sm:px-8">
            {isSyncingHistory ? <ConversationSyncBanner /> : null}
            <ThreadPrimitive.Empty>
              {showInitialWorkspaceShell ? (
                <InitialAssistantShell />
              ) : (
                <AssistantWelcome
                  disabled={isBootstrapping || isSwitchingTrips}
                  hasWorkspace={hasWorkspace}
                  hasError={hasError}
                  profileContext={profileContext}
                />
              )}
            </ThreadPrimitive.Empty>

            <ThreadMessagesStack hasHydratedMessages={hasHydratedMessages} />
          </ThreadPrimitive.Viewport>

          <Composer
            disabled={isBootstrapping || isSwitchingTrips || !hasWorkspace || hasError}
            disabledPlaceholder={
              showInitialWorkspaceShell
                ? "Preparing your travel planning workspace..."
                : isBootstrapping
                  ? "Attaching the planner workspace..."
                : isSwitchingTrips
                  ? "Opening the selected trip..."
                  : !hasWorkspace
                    ? "Opening this trip..."
                    : "Resolve the workspace issue before sending."
            }
          />
        </ThreadPrimitive.Root>
        {isSwitchingTrips ? (
          <TripSwitchOverlay requestedTripId={requestedTripId} />
        ) : null}
      </section>
    </AssistantRuntimeProvider>
  );
}

function ThreadMessagesStack({
  hasHydratedMessages,
}: {
  hasHydratedMessages: boolean;
}) {
  const runtimeMessageCount = useThread((state) => state.messages.length);
  const hasConversationMessages = hasHydratedMessages || runtimeMessageCount > 0;

  return (
    <div
      className={`mx-auto flex w-full max-w-[52rem] flex-col gap-6 ${
        hasConversationMessages ? "mt-auto pb-6" : "pb-4"
      }`}
    >
      <ThreadPrimitive.Messages
        components={{
          UserMessage,
          AssistantMessage,
        }}
      />
    </div>
  );
}

function ThreadHydrationSync({
  tripId,
  initialMessages,
  hydratedMessages,
}: {
  tripId: string | null;
  initialMessages: PersistedThreadMessage[];
  hydratedMessages: ReturnType<typeof buildThreadSeedMessages>;
}) {
  const runtime = useThreadRuntime();
  const runtimeMessages = useThread((state) => state.messages);
  const isRunning = useThread((state) => state.isRunning);
  const didInitializeRef = useRef(false);
  const activeTripIdRef = useRef<string | null>(tripId);
  const lastHydratedSnapshotRef = useRef(
    serializePersistedThreadMessages(initialMessages),
  );
  const initialSnapshot = useMemo(
    () => serializePersistedThreadMessages(initialMessages),
    [initialMessages],
  );
  const runtimeSnapshot = useMemo(
    () =>
      serializePersistedThreadMessages(
        extractPersistedThreadMessages(runtimeMessages),
      ),
    [runtimeMessages],
  );

  useEffect(() => {
    if (!didInitializeRef.current) {
      didInitializeRef.current = true;
      activeTripIdRef.current = tripId;
      lastHydratedSnapshotRef.current = initialSnapshot;
      return;
    }

    const tripChanged = activeTripIdRef.current !== tripId;

    if (tripChanged) {
      const previousTripId = activeTripIdRef.current;
      const preservingNewChatHandoff =
        isEphemeralTripId(previousTripId) &&
        Boolean(tripId && !isEphemeralTripId(tripId)) &&
        runtimeMessages.length > 0;

      if (preservingNewChatHandoff) {
        activeTripIdRef.current = tripId;
        lastHydratedSnapshotRef.current = runtimeSnapshot;
        return;
      }

      if (isRunning) {
        return;
      }

      activeTripIdRef.current = tripId;
      lastHydratedSnapshotRef.current = initialSnapshot;
      runtime.reset(hydratedMessages);
      void runtime.composer.reset();
      return;
    }

    const historySeedChanged =
      initialSnapshot !== lastHydratedSnapshotRef.current &&
      runtimeSnapshot === lastHydratedSnapshotRef.current;

    if (!historySeedChanged || isRunning) {
      return;
    }

    lastHydratedSnapshotRef.current = initialSnapshot;
    runtime.reset(hydratedMessages);
  }, [
    hydratedMessages,
    initialSnapshot,
    isRunning,
    runtime,
    runtimeMessages.length,
    runtimeSnapshot,
    tripId,
  ]);

  return null;
}

function PersistedThreadStateSync({ tripId }: { tripId: string | null }) {
  const messages = useThread((state) => state.messages);
  const persistTimeoutRef = useRef<number | null>(null);
  const lastPersistedSnapshotRef = useRef<string | null>(null);

  useEffect(() => {
    if (persistTimeoutRef.current !== null) {
      window.clearTimeout(persistTimeoutRef.current);
      persistTimeoutRef.current = null;
    }

    lastPersistedSnapshotRef.current = null;
  }, [tripId]);

  useEffect(() => {
    if (!tripId) {
      return;
    }

    const persistedMessages = extractPersistedThreadMessages(messages);
    const serializedMessages =
      serializePersistedThreadMessages(persistedMessages);

    if (serializedMessages === lastPersistedSnapshotRef.current) {
      return;
    }

    if (persistTimeoutRef.current !== null) {
      window.clearTimeout(persistTimeoutRef.current);
    }

    persistTimeoutRef.current = window.setTimeout(() => {
      writeCachedThreadMessages(tripId, persistedMessages);
      lastPersistedSnapshotRef.current = serializedMessages;
      persistTimeoutRef.current = null;
    }, 220);

    return () => {
      if (persistTimeoutRef.current !== null) {
        window.clearTimeout(persistTimeoutRef.current);
        persistTimeoutRef.current = null;
      }
    };
  }, [messages, tripId]);

  return null;
}

function EmptyThreadViewportReset() {
  const messages = useThread((state) => state.messages);

  useEffect(() => {
    if (messages.length > 0) {
      return;
    }

    let frame = 0;
    let nestedFrame = 0;
    let timeout = 0;

    const resetViewport = () => {
      const viewport = document.querySelector<HTMLElement>(
        ".chat-workspace-scroll",
      );
      viewport?.scrollTo({ top: 0, behavior: "auto" });
    };

    resetViewport();
    frame = window.requestAnimationFrame(() => {
      resetViewport();
      nestedFrame = window.requestAnimationFrame(() => {
        resetViewport();
      });
    });
    timeout = window.setTimeout(() => {
      resetViewport();
    }, 96);

    return () => {
      window.cancelAnimationFrame(frame);
      window.cancelAnimationFrame(nestedFrame);
      window.clearTimeout(timeout);
    };
  }, [messages.length]);

  return null;
}

function ChatViewportAutoScroll() {
  const messageCount = useThread((state) => state.messages.length);
  const isRunning = useThread((state) => state.isRunning);

  useEffect(() => {
    if (messageCount === 0) {
      return;
    }

    const viewport = document.querySelector<HTMLElement>(
      ".chat-workspace-scroll",
    );

    if (!viewport) {
      return;
    }

    const distanceFromBottom =
      viewport.scrollHeight - viewport.clientHeight - viewport.scrollTop;
    const shouldStickToBottom =
      messageCount <= 2 || isRunning || distanceFromBottom < 320;

    if (!shouldStickToBottom) {
      return;
    }

    const prefersReducedMotion = window.matchMedia(
      "(prefers-reduced-motion: reduce)",
    ).matches;
    const behavior: ScrollBehavior = prefersReducedMotion ? "auto" : "smooth";
    const frame = window.requestAnimationFrame(() => {
      viewport.scrollTo({ top: viewport.scrollHeight, behavior });
    });
    const timeout = window.setTimeout(() => {
      viewport.scrollTo({ top: viewport.scrollHeight, behavior: "auto" });
    }, 180);

    return () => {
      window.cancelAnimationFrame(frame);
      window.clearTimeout(timeout);
    };
  }, [isRunning, messageCount]);

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

function TripSwitchOverlay({
  requestedTripId,
}: {
  requestedTripId: string | null;
}) {
  return (
    <div className="pointer-events-none absolute inset-x-0 top-0 z-10 flex justify-center px-6 pt-8">
      <div className="trip-switch-overlay-card inline-flex items-center gap-2 rounded-full border border-border/70 bg-background/94 px-3 py-1.5 text-[0.78rem] text-muted-foreground shadow-[var(--chat-shadow-soft)]">
        <span className="h-1.5 w-1.5 shrink-0 rounded-full bg-[color:var(--accent)]" />
        <span>
          Opening {requestedTripId ? "the selected trip" : "the next trip"}
        </span>
      </div>
    </div>
  );
}

function InitialAssistantShell() {
  return (
    <div className="mx-auto w-full max-w-[52rem] px-1 pb-6 pt-2">
      <div className="overflow-hidden rounded-[1.4rem] border border-[color:var(--chat-rail-border)] bg-[color:var(--chat-rail-surface-strong)] shadow-[var(--chat-shadow-soft)]">
        <div className="border-b border-[color:var(--chat-rail-border)] px-5 py-4 sm:px-6">
          <div className="h-3 w-28 animate-pulse rounded-full bg-[color:var(--chat-rail-control-bg)]" />
          <div className="mt-4 max-w-2xl space-y-3">
            <div className="h-8 w-[62%] animate-pulse rounded-full bg-[color:var(--chat-rail-control-bg)]/88" />
            <div className="space-y-2">
              <div className="h-3 w-full animate-pulse rounded-full bg-[color:var(--chat-rail-control-bg)]/72" />
              <div className="h-3 w-[86%] animate-pulse rounded-full bg-[color:var(--chat-rail-control-bg)]/56" />
            </div>
          </div>
        </div>

        <div className="grid gap-3 px-5 py-4 sm:grid-cols-3 sm:px-6">
          {Array.from({ length: 3 }).map((_, index) => (
            <div
              key={index}
              className="rounded-[1.1rem] border border-[color:var(--chat-rail-border)] bg-[color:var(--chat-rail-surface)] px-4 py-4"
            >
              <div className="h-3 w-24 animate-pulse rounded-full bg-[color:var(--chat-rail-control-bg)]/90" />
              <div className="mt-3 space-y-2">
                <div className="h-4 w-28 animate-pulse rounded-full bg-[color:var(--chat-rail-control-bg)]/70" />
                <div className="h-3 w-full animate-pulse rounded-full bg-[color:var(--chat-rail-control-bg)]/58" />
                <div className="h-3 w-[74%] animate-pulse rounded-full bg-[color:var(--chat-rail-control-bg)]/46" />
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="grid gap-3 sm:grid-cols-2">
        {Array.from({ length: 4 }).map((_, index) => (
          <div
            key={index}
            className="rounded-[1.15rem] border border-[color:var(--chat-rail-border)] bg-[color:var(--chat-rail-surface)] px-4 py-4 shadow-[var(--chat-shadow-soft)]"
          >
            <div className="flex items-start justify-between gap-3">
              <div className="h-9 w-9 animate-pulse rounded-lg border border-[color:var(--chat-rail-border)] bg-[color:var(--chat-rail-control-bg)]" />
              <div className="h-3 w-12 animate-pulse rounded-full bg-[color:var(--chat-rail-control-bg)]/80" />
            </div>
            <div className="mt-4 space-y-2">
              <div className="h-4 w-32 animate-pulse rounded-full bg-[color:var(--chat-rail-control-bg)]/90" />
              <div className="h-3 w-full animate-pulse rounded-full bg-[color:var(--chat-rail-control-bg)]/68" />
              <div className="h-3 w-[78%] animate-pulse rounded-full bg-[color:var(--chat-rail-control-bg)]/52" />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

// eslint-disable-next-line @typescript-eslint/no-unused-vars
function AssistantWelcomeLegacy({
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
    <div className="mx-auto flex w-full max-w-[52rem] flex-col gap-5 px-1 pb-6 pt-2">
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
  const starterPrompts: Array<{
    title: string;
    description: string;
    prompt: string;
    image: string;
    disabled: boolean;
  }> = [
    {
      title: "Kyoto food and culture",
      description: profileContext?.home_airport
        ? `A calm 5-day route from ${profileContext.home_airport}.`
        : "A calm 5-day route with temples and markets.",
      prompt: profileContext?.home_airport
        ? `Plan a calm 5-day food and culture trip to Kyoto from ${profileContext.home_airport} for two adults.`
        : "Plan a calm 5-day food and culture trip to Kyoto for two adults.",
      image:
        "https://images.unsplash.com/photo-1493976040374-85c8e12f0c0e?auto=format&fit=crop&w=640&q=72",
      disabled: disabled || !hasWorkspace,
    },
    {
      title: "Warm September cities",
      description: "A 4-night city break with a clear best pick.",
      prompt:
        "I have 4 nights in late September. Suggest three warm European cities and help me choose between them.",
      image:
        "https://images.unsplash.com/photo-1516483638261-f4dbaf036963?auto=format&fit=crop&w=640&q=76",
      disabled: disabled || !hasWorkspace,
    },
    {
      title: "Lisbon or Porto",
      description: profileContext?.preferred_currency
        ? `A relaxed long weekend planned in ${profileContext.preferred_currency}.`
        : "A relaxed long weekend with an easy comparison.",
      prompt: profileContext?.preferred_currency
        ? `Help me compare Lisbon and Porto for a relaxed long weekend, and keep the budget in ${profileContext.preferred_currency}.`
        : "Help me compare Lisbon and Porto for a relaxed long weekend.",
      image:
        "https://images.unsplash.com/photo-1555881400-74d7acaacd8b?auto=format&fit=crop&w=640&q=76",
      disabled: disabled || !hasWorkspace,
    },
    {
      title: "Barcelona family days",
      description: "Central stays, easy pacing, and rainy-day backups.",
      prompt:
        "Plan a weather-aware family trip to Barcelona with central stays, easy days, and backup activities.",
      image:
        "https://images.unsplash.com/photo-1583422409516-2895a77efded?auto=format&fit=crop&w=640&q=76",
      disabled: disabled || !hasWorkspace,
    },
  ];

  return (
    <div className="chat-welcome-enter mx-auto flex min-h-[clamp(26rem,58dvh,34rem)] w-full max-w-[52rem] flex-col justify-end px-1 pb-4 pt-8">
      <div className="space-y-4">
        <div className="flex max-w-[44rem] items-start gap-3">
          <div className="mt-0.5 flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-[color:color-mix(in_srgb,var(--accent)_12%,transparent)] text-[color:var(--accent)] shadow-[var(--chat-shadow-card)] ring-1 ring-[color:color-mix(in_srgb,var(--accent)_14%,transparent)]">
            <Bot className="h-4 w-4" />
          </div>
          <div className="rounded-[1rem] border border-border/70 bg-background/92 px-5 py-4 shadow-[var(--chat-shadow-soft)] dark:bg-card/96">
            <p className="text-[length:var(--chat-size-body)] font-medium leading-[var(--chat-line-body)] text-foreground">
              {`Tell me the trip you're trying to make, ${greetingName}.`}
            </p>
            <p className="mt-1 text-sm leading-6 text-muted-foreground">
              {contextLine}
            </p>
          </div>
        </div>

        <div className="max-w-[44rem] pl-12">
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

        <div className="grid max-w-[44rem] gap-x-5 gap-y-1 pl-12 sm:grid-cols-2">
          {starterPrompts.map((starter, index) => {
            return (
              <ThreadPrimitive.Suggestion
                key={starter.title}
                className="chat-starter-option group flex min-h-16 w-full items-center gap-3 border-b border-[color:var(--chat-rail-border)] py-2.5 text-left disabled:cursor-not-allowed disabled:opacity-60"
                prompt={starter.prompt}
                autoSend
                disabled={starter.disabled}
                style={{ "--starter-index": index } as CSSProperties}
              >
                <span
                  aria-hidden="true"
                  className="h-14 w-16 shrink-0 rounded-lg bg-cover bg-center"
                  style={{ backgroundImage: `url("${starter.image}")` }}
                />
                <span className="min-w-0 flex-1">
                  <span className="text-[0.92rem] font-medium leading-5 text-foreground">
                    {starter.title}
                  </span>
                  <span className="mt-1 line-clamp-2 text-[0.8rem] leading-5 text-muted-foreground">
                    {starter.description}
                  </span>
                </span>
              </ThreadPrimitive.Suggestion>
            );
          })}
        </div>
      </div>
    </div>
  );
}

function UserMessage() {
  return (
    <MessagePrimitive.Root className="chat-message-enter flex justify-end">
      <div className="flex max-w-[min(86%,44rem)] items-end gap-3">
        <div className="chat-user-bubble-enter min-w-0 flex-1 rounded-[1.1rem] rounded-br-md border border-[color:color-mix(in_srgb,var(--accent)_24%,transparent)] bg-[color:color-mix(in_srgb,var(--accent)_10%,var(--color-background))] px-5 py-4 text-[length:var(--chat-size-body)] leading-[var(--chat-line-body)] text-foreground shadow-[var(--chat-shadow-card)]">
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
  const status = useMessage((m) => m.status);
  const isRunning = status?.type === "running";

  return (
    <MessagePrimitive.Root className="chat-message-enter flex flex-col items-start gap-3">
      <div className="flex items-start gap-3">
        <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-[color:color-mix(in_srgb,var(--accent)_12%,transparent)] text-[color:var(--accent)] shadow-[var(--chat-shadow-card)] ring-1 ring-[color:color-mix(in_srgb,var(--accent)_14%,transparent)]">
          <Bot className="h-4 w-4" />
        </div>
        <div className="max-w-[min(100%,48rem)]">
          {isRunning ? (
            <div className="chat-assistant-bubble-enter flex items-center py-2">
              <AgentThinkingTyping />
            </div>
          ) : (
            <div className="chat-assistant-bubble-enter overflow-hidden rounded-[1rem] border border-border/70 bg-background/92 shadow-[var(--chat-shadow-soft)] dark:bg-card/96">
              <div className="px-5 py-4 text-[length:var(--chat-size-body)] leading-[var(--chat-line-body)] text-foreground">
                <AssistantMessageContent />
              </div>
            </div>
          )}
        </div>
      </div>
    </MessagePrimitive.Root>
  );
}

function AssistantMessageContent() {
  const text = useMessage((message) =>
    message.content
      .filter((part) => part.type === "text")
      .map((part) => part.text)
      .join("\n")
      .trim(),
  );

  if (!text) {
    return <MessagePrimitive.Parts />;
  }

  const blocks = text.split(/\n{2,}/).filter((block) => block.trim());

  return (
    <div className="space-y-3">
      {blocks.map((block, index) => (
        <AssistantMessageBlock key={`${index}-${block.slice(0, 20)}`} block={block} />
      ))}
    </div>
  );
}

function AssistantMessageBlock({ block }: { block: string }) {
  const lines = block.split("\n").map((line) => line.trim()).filter(Boolean);
  if (lines.length === 0) {
    return null;
  }

  const heading = parseBoldHeading(lines[0]);
  if (heading) {
    const bodyLines = lines.slice(1);
    return (
      <div className="space-y-2">
        <p className="font-semibold text-[var(--planner-board-text)]">{heading}</p>
        {bodyLines.length > 0 ? (
          <AssistantMessageLines lines={bodyLines} />
        ) : null}
      </div>
    );
  }

  return <AssistantMessageLines lines={lines} />;
}

function AssistantMessageLines({ lines }: { lines: string[] }) {
  if (lines.every((line) => line.startsWith("- "))) {
    return (
      <ul className="space-y-2">
        {lines.map((line) => (
          <li
            key={line}
            className="relative pl-4 leading-[var(--chat-line-body)] before:absolute before:left-0 before:top-[0.7em] before:h-1.5 before:w-1.5 before:rounded-full before:bg-[var(--planner-board-cta)]"
          >
            {renderInlineBold(line.slice(2))}
          </li>
        ))}
      </ul>
    );
  }

  return (
    <p className="whitespace-pre-line">
      {renderInlineBold(lines.join("\n"))}
    </p>
  );
}

function parseBoldHeading(line: string) {
  const match = line.match(/^\*\*([^*]+)\*\*$/);
  return match?.[1] ?? null;
}

function renderInlineBold(text: string): ReactNode[] {
  return text.split(/(\*\*[^*]+\*\*)/g).map((segment, index) => {
    if (segment.startsWith("**") && segment.endsWith("**")) {
      return (
        <strong key={`${segment}-${index}`} className="font-semibold text-foreground">
          {segment.slice(2, -2)}
        </strong>
      );
    }
    return segment;
  });
}

function Composer({
  disabled,
  disabledPlaceholder,
}: {
  disabled: boolean;
  disabledPlaceholder: string;
}) {
  const isRunning = useThread((state) => state.isRunning);
  const composerRuntime = useComposerRuntime({ optional: true });
  const composerIsEmpty = useComposer((state) => state.isEmpty);
  const sendDisabled = disabled || isRunning || composerIsEmpty || !composerRuntime;
  const showCancel = Boolean(composerRuntime && isRunning);
  const [sendPulse, setSendPulse] = useState(false);
  const sendPulseTimeoutRef = useRef<number | null>(null);

  useEffect(() => {
    return () => {
      if (sendPulseTimeoutRef.current !== null) {
        window.clearTimeout(sendPulseTimeoutRef.current);
      }
    };
  }, []);

  const handleSend = () => {
    if (sendDisabled || !composerRuntime) {
      return;
    }

    setSendPulse(true);
    if (sendPulseTimeoutRef.current !== null) {
      window.clearTimeout(sendPulseTimeoutRef.current);
    }
    sendPulseTimeoutRef.current = window.setTimeout(() => {
      setSendPulse(false);
      sendPulseTimeoutRef.current = null;
    }, 420);
    composerRuntime.send();
  };

  return (
    <ComposerPrimitive.Root className="bg-[color:var(--chat-pane-bg)] px-4 py-3 sm:px-8">
      <div className="mx-auto w-full max-w-[52rem]">
        <div
          className={`flex min-h-14 items-center gap-2.5 rounded-xl border border-[color:var(--chat-rail-border-strong)] bg-[color:var(--chat-rail-control-bg)] px-4 py-2 shadow-[var(--chat-shadow-card)] transition-colors focus-within:border-[color:var(--accent)]/50 ${
            sendPulse ? "chat-composer-sent" : ""
          }`}
        >
          <ComposerPrimitive.Input
            name="trip-message"
            rows={1}
            placeholder={
              disabled
                ? disabledPlaceholder
                : "Message Wandrix..."
            }
            disabled={disabled}
            className="min-h-9 max-h-32 min-w-0 flex-1 resize-none bg-transparent px-0 py-1.5 text-[0.95rem] leading-6 text-foreground outline-none placeholder:text-muted-foreground disabled:cursor-not-allowed disabled:text-muted-foreground"
          />
          {showCancel ? (
            <button
              type="button"
              onClick={() => {
                composerRuntime?.cancel();
              }}
              className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-[color:var(--accent)] text-[color:var(--chat-composer-on-accent)] shadow-[var(--chat-shadow-card)] transition-[opacity,transform] hover:-translate-y-0.5 hover:opacity-95 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[color:var(--accent)]/20"
              aria-label="Stop generating"
            >
              <span className="h-3.5 w-3.5 rounded-[0.18rem] bg-[color:var(--chat-composer-on-accent)]" />
            </button>
          ) : (
            <button
              type="button"
              disabled={sendDisabled}
              onClick={handleSend}
              className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-[color:var(--accent)] text-[color:var(--chat-composer-on-accent)] shadow-[var(--chat-shadow-card)] transition-[opacity,transform] hover:-translate-y-0.5 hover:opacity-95 disabled:cursor-not-allowed disabled:opacity-100 disabled:hover:translate-y-0"
              aria-label="Send message"
            >
              <ArrowUp
                className="h-5 w-5"
                strokeWidth={2.4}
                style={{
                  color: "#ffffff",
                  stroke: "#ffffff",
                }}
              />
            </button>
          )}
        </div>
      </div>
    </ComposerPrimitive.Root>
  );
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
  onEnsurePersistedTrip: (
    sourceTripId?: string | null,
  ) => Promise<PlannerWorkspaceState | null>;
  onActivatePersistedTrip: (
    workspace: PlannerWorkspaceState,
    sourceTripId?: string | null,
  ) => void;
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
    const currentLocationContext = await resolvePlannerLocationForTurn({
      tripId: activeTripId,
      profileContext,
      tripDraft: workspace?.tripDraft ?? null,
    });

    if (workspace?.isEphemeral && !pendingBoardAction) {
      try {
        const openingTurn = await getOpeningTurnResponse(
          {
            message: latestText,
            profile_context: profileContext ?? undefined,
            current_location_context: currentLocationContext ?? undefined,
          },
          authSnapshot.accessToken,
        );

        if (!openingTurn.should_start_trip) {
          const persistedWorkspace = await onEnsurePersistedTrip(workspace.trip.trip_id);
          const resolvedTripId = persistedWorkspace?.trip.trip_id ?? null;

          if (persistedWorkspace && resolvedTripId) {
            cacheAssistantTurn(resolvedTripId, latestText, openingTurn.message);
            onActivatePersistedTrip(persistedWorkspace, workspace.trip.trip_id);
          }

          return openingTurn.message;
        }
      } catch {
        // Fall through to the full persisted planner flow if the lightweight opening gate is unavailable.
      }
    }

    const persistedWorkspace =
      workspace?.isEphemeral
        ? await onEnsurePersistedTrip(workspace.trip.trip_id)
        : workspace;
    const resolvedTripId = persistedWorkspace?.trip.trip_id ?? activeTripId;

    if (!resolvedTripId) {
      return "I could not prepare a real trip yet, so I’m holding here until the workspace is ready.";
    }

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

    const shouldSurfacePersistedWorkspace =
      Boolean(workspace?.isEphemeral && persistedWorkspace) &&
      shouldActivatePersistedTrip(response.trip_draft);

    if (workspace?.isEphemeral && persistedWorkspace) {
      cacheAssistantTurn(resolvedTripId, latestText, response.message);

      if (shouldSurfacePersistedWorkspace) {
        onActivatePersistedTrip(
          {
            ...persistedWorkspace,
            trip: {
              ...persistedWorkspace.trip,
              title: response.trip_draft.title,
            },
            tripDraft: response.trip_draft,
          },
          workspace.trip.trip_id,
        );
      }
    }

    if (!workspace?.isEphemeral || shouldSurfacePersistedWorkspace) {
      onDraftUpdated(response.trip_draft);
    }

    return response.message;
  } catch (error) {
    return error instanceof Error
      ? error.message
      : "The backend conversation bridge failed unexpectedly.";
  }
}

function buildWelcomeContextLine(profileContext: PlannerProfileContext | null) {
  if (!profileContext) {
    return "A place, mood, rough date, or constraint is enough. The board stays editable as the plan takes shape.";
  }

  const contextBits = [
    profileContext.home_airport
      ? `starting from ${profileContext.home_airport}`
      : null,
    profileContext.preferred_currency
      ? `planning in ${profileContext.preferred_currency}`
      : null,
    profileContext.home_city
      ? `using ${profileContext.home_city}${
          profileContext.home_country ? `, ${profileContext.home_country}` : ""
        } as your home base`
      : profileContext.home_country
        ? `using ${profileContext.home_country} as your home base`
        : null,
  ].filter((contextBit): contextBit is string => Boolean(contextBit));

  if (contextBits.length === 0) {
    return "A place, mood, rough date, or constraint is enough. The board stays editable as the plan takes shape.";
  }

  return `I’ll start by ${formatWelcomeContextBits(contextBits)} unless you tell me something different for this trip.`;
}

function formatWelcomeContextBits(contextBits: string[]) {
  if (contextBits.length <= 1) {
    return contextBits[0] ?? "using your travel preferences";
  }

  if (contextBits.length === 2) {
    return `${contextBits[0]} and ${contextBits[1]}`;
  }

  return `${contextBits.slice(0, -1).join(", ")}, and ${
    contextBits[contextBits.length - 1]
  }`;
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
