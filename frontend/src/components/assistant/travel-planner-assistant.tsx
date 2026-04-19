"use client";

import { useEffect, useMemo, useState } from "react";
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

import { sendTripConversationMessage } from "@/lib/api/conversation";
import { getTripDraft } from "@/lib/api/trips";
import { createClient as createSupabaseBrowserClient } from "@/lib/supabase/client";
import type { PlannerWorkspaceState } from "@/types/planner-workspace";
import type { PlannerProfileContext } from "@/types/conversation";
import type { TripDraft } from "@/types/trip-draft";

type TravelPlannerAssistantProps = {
  workspace: PlannerWorkspaceState | null;
  isBootstrapping: boolean;
  workspaceError: string | null;
  onDraftUpdated: (tripDraft: TripDraft) => void;
};

type PersistedThreadMessage = {
  id?: string;
  role: "assistant" | "user" | "system";
  createdAt?: string;
  content: string;
};

const CHAT_HISTORY_STORAGE_PREFIX = "wandrix:chat-history:";

export function TravelPlannerAssistant({
  workspace,
  isBootstrapping,
  workspaceError,
  onDraftUpdated,
}: TravelPlannerAssistantProps) {
  const [profileContext, setProfileContext] = useState<PlannerProfileContext | null>(
    null,
  );
  const [savedMessages, setSavedMessages] = useState<PersistedThreadMessage[] | null>(
    null,
  );

  const tripId = workspace?.trip.trip_id ?? null;

  useEffect(() => {
    async function loadSavedMessages() {
      if (!tripId) {
        setSavedMessages([]);
        return;
      }

      try {
        const rawValue = window.localStorage.getItem(
          `${CHAT_HISTORY_STORAGE_PREFIX}${tripId}`,
        );

        if (!rawValue) {
          setSavedMessages([]);
          return;
        }

        const parsed = JSON.parse(rawValue);

        if (!Array.isArray(parsed)) {
          setSavedMessages([]);
          return;
        }

        setSavedMessages(
          parsed.flatMap((entry) => {
            if (
              !entry ||
              typeof entry !== "object" ||
              !("role" in entry) ||
              !("content" in entry)
            ) {
              return [];
            }

            const candidate = entry as Record<string, unknown>;
            const role = candidate.role;
            const content = candidate.content;

            if (
              (role !== "assistant" && role !== "user" && role !== "system") ||
              typeof content !== "string"
            ) {
              return [];
            }

            return [
              {
                id: typeof candidate.id === "string" ? candidate.id : undefined,
                role,
                content,
                createdAt:
                  typeof candidate.createdAt === "string"
                    ? candidate.createdAt
                    : undefined,
              } satisfies PersistedThreadMessage,
            ];
          }),
        );
      } catch {
        setSavedMessages([]);
      }
    }

    void loadSavedMessages();
  }, [tripId]);

  useEffect(() => {
    let cancelled = false;

    async function loadProfileContext() {
      const supabase = createSupabaseBrowserClient();
      const {
        data: { session },
      } = await supabase.auth.getSession();

      const userId = session?.user?.id;
      const userMetadata =
        session?.user?.user_metadata && typeof session.user.user_metadata === "object"
          ? (session.user.user_metadata as Record<string, unknown>)
          : {};

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
  }, []);

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
          isBootstrapping,
          workspace,
          workspaceError,
          latestText,
          profileContext,
          onDraftUpdated,
        });

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
    [isBootstrapping, onDraftUpdated, profileContext, workspace, workspaceError],
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
      profileContext={profileContext}
      isBootstrapping={isBootstrapping}
      hasWorkspace={Boolean(workspace)}
      hasError={Boolean(workspaceError)}
    />
  );
}

function TravelPlannerAssistantRuntime({
  adapter,
  tripId,
  initialMessages,
  profileContext,
  isBootstrapping,
  hasWorkspace,
  hasError,
}: {
  adapter: ChatModelAdapter;
  tripId: string | null;
  initialMessages: PersistedThreadMessage[];
  profileContext: PlannerProfileContext | null;
  isBootstrapping: boolean;
  hasWorkspace: boolean;
  hasError: boolean;
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
      <section className="relative flex h-full min-h-0 flex-col bg-[color:var(--chat-pane-bg)]">
        <ThreadPrimitive.Root className="flex min-h-0 flex-1 flex-col overflow-hidden">
          <ThreadPrimitive.Viewport className="chat-workspace-scroll flex min-h-0 flex-1 flex-col overflow-y-auto px-4 py-6 sm:px-8">
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

          <Composer />
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

    window.localStorage.setItem(
      `${CHAT_HISTORY_STORAGE_PREFIX}${tripId}`,
      JSON.stringify(persistedMessages),
    );
  }, [messages, tripId]);

  return null;
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

function Composer() {
  return (
    <ComposerPrimitive.Root className="border-t border-[color:var(--chat-rail-border)] bg-[color:var(--chat-pane-bg)] px-4 pb-4 pt-3 sm:px-8">
      <div className="mx-auto w-full max-w-[52rem]">
        <div className="overflow-hidden rounded-xl border border-[color:var(--chat-rail-border-strong)] bg-[color:var(--chat-rail-surface-strong)] p-2">
          <div className="flex items-end gap-2">
            <div className="flex min-w-0 flex-1 rounded-lg border border-[color:var(--chat-rail-border)] bg-[color:var(--chat-rail-control-bg)] px-3 py-2.5 transition-colors focus-within:border-[color:var(--accent)]/45">
              <ComposerPrimitive.Input
                rows={1}
                placeholder="Continue planning your trip..."
                className="min-h-12 max-h-40 w-full resize-none bg-transparent px-1 py-0.5 text-sm leading-7 text-foreground outline-none placeholder:text-muted-foreground"
              />
            </div>
            <ComposerPrimitive.Send asChild>
              <button
                type="button"
                className="flex h-12 w-12 shrink-0 items-center justify-center rounded-lg border border-[color:var(--chat-rail-border)] bg-[linear-gradient(135deg,var(--accent),var(--accent2))] text-white transition-opacity hover:opacity-95"
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
  isBootstrapping,
  workspace,
  workspaceError,
  latestText,
  profileContext,
  onDraftUpdated,
}: {
  isBootstrapping: boolean;
  workspace: PlannerWorkspaceState | null;
  workspaceError: string | null;
  latestText: string;
  profileContext: PlannerProfileContext | null;
  onDraftUpdated: (tripDraft: TripDraft) => void;
}) {
  if (isBootstrapping || workspaceError || !workspace || !latestText) {
    return buildFallbackAssistantReply({
      isBootstrapping,
      workspace,
      workspaceError,
      latestText,
    });
  }

  const supabase = createSupabaseBrowserClient();
  const {
    data: { session },
    error: sessionError,
  } = await supabase.auth.getSession();

  if (sessionError || !session?.access_token) {
    return "I can render the chat shell, but I could not read a valid Supabase access token for the backend conversation call.";
  }

  try {
    const response = await sendTripConversationMessage(
      workspace.trip.trip_id,
      {
        message: latestText,
        profile_context: profileContext ?? undefined,
      },
      session.access_token,
    );
    const updatedDraft = await getTripDraft(
      workspace.trip.trip_id,
      session.access_token,
    );
    onDraftUpdated(updatedDraft);

    return response.message;
  } catch (error) {
    return error instanceof Error
      ? error.message
      : "The backend conversation bridge failed unexpectedly.";
  }
}

function buildWelcomeContextLine(profileContext: PlannerProfileContext | null) {
  if (!profileContext) {
    return "Tell me where you want to go, how you want the trip to feel, and I’ll start shaping it with the live board on the right.";
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
    return "Tell me where you want to go, how you want the trip to feel, and I’ll start shaping it with the live board on the right.";
  }

  return `I can start with ${contextBits.join(", ")} as soft defaults, but anything you say in chat will take priority for this trip.`;
}

function buildFallbackAssistantReply({
  isBootstrapping,
  workspace,
  workspaceError,
  latestText,
}: {
  isBootstrapping: boolean;
  workspace: PlannerWorkspaceState | null;
  workspaceError: string | null;
  latestText: string;
}) {
  if (isBootstrapping) {
    return "I'm waiting for the trip workspace to finish booting before I attach this conversation to it.";
  }

  if (workspaceError) {
    return `I can render the chat shell, but the trip workspace still needs fixing first: ${workspaceError}`;
  }

  if (!workspace) {
    return "I need a signed-in trip workspace before I can attach this conversation to a real trip and thread.";
  }

  if (!latestText) {
    return `I'm attached to trip ${workspace.trip.trip_id}. The assistant-ui shell is working, and the next step is connecting this thread to the real LangGraph planner.`;
  }

  return `I'm routing your message to the backend trip conversation bridge for trip ${workspace.trip.trip_id}.`;
}
