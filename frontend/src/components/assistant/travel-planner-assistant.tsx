"use client";

import { useMemo } from "react";
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
  useLocalRuntime,
  type ChatModelAdapter,
} from "@assistant-ui/react";

import { sendTripConversationMessage } from "@/lib/api/conversation";
import { getTripDraft } from "@/lib/api/trips";
import { createClient as createSupabaseBrowserClient } from "@/lib/supabase/client";
import type { PlannerWorkspaceState } from "@/types/planner-workspace";
import type { TripDraft } from "@/types/trip-draft";

type TravelPlannerAssistantProps = {
  workspace: PlannerWorkspaceState | null;
  isBootstrapping: boolean;
  workspaceError: string | null;
  onDraftUpdated: (tripDraft: TripDraft) => void;
};

export function TravelPlannerAssistant({
  workspace,
  isBootstrapping,
  workspaceError,
  onDraftUpdated,
}: TravelPlannerAssistantProps) {
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
    [isBootstrapping, onDraftUpdated, workspace, workspaceError],
  );

  const runtime = useLocalRuntime(adapter);

  return (
    <AssistantRuntimeProvider runtime={runtime}>
      <section className="relative flex h-full min-h-0 flex-col bg-[color:var(--chat-pane-bg)]">
        <ThreadPrimitive.Root className="flex min-h-0 flex-1 flex-col overflow-hidden">
          <ThreadPrimitive.Viewport className="chat-workspace-scroll flex min-h-0 flex-1 flex-col overflow-y-auto px-4 py-6 sm:px-8">
            <ThreadPrimitive.Empty>
              <AssistantWelcome
                disabled={isBootstrapping}
                hasWorkspace={Boolean(workspace)}
                hasError={Boolean(workspaceError)}
              />
            </ThreadPrimitive.Empty>

            <div className="mx-auto mt-auto flex w-full max-w-4xl flex-col gap-6 pb-40">
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

function AssistantWelcome({
  disabled,
  hasWorkspace,
  hasError,
}: {
  disabled: boolean;
  hasWorkspace: boolean;
  hasError: boolean;
}) {
  return (
    <div className="mx-auto flex h-full min-h-[24rem] w-full max-w-4xl flex-col justify-end gap-6 px-1 pt-2">
      <div className="space-y-2">
        <div className="text-xs font-medium uppercase tracking-[0.22em] text-[color:var(--accent)]">
          Wandrix planner
        </div>
        <div className="space-y-2">
          <div className="text-sm font-semibold text-foreground">Start with a trip idea</div>
          <p className="max-w-2xl text-sm text-muted-foreground">
            Pick a starting point and refine the details in chat.
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
          prompt="Plan a 5-day food and culture trip to Kyoto for two adults."
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
            Plan a 5-day food and culture trip to Kyoto for two adults.
          </div>
        </ThreadPrimitive.Suggestion>
        <ThreadPrimitive.Suggestion
          className="group rounded-xl border border-[color:var(--chat-rail-border)] bg-[color:var(--chat-rail-surface)] px-4 py-4 text-left transition-colors hover:border-[color:var(--chat-rail-border-strong)] hover:bg-[color:var(--chat-rail-surface-strong)] disabled:cursor-not-allowed disabled:opacity-60"
          prompt="Help me shape a luxury long weekend in Lisbon with flights and hotel ideas."
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
            Help me shape a luxury long weekend in Lisbon with flights and hotel ideas.
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
      <div className="mx-auto w-full max-w-4xl">
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
  onDraftUpdated,
}: {
  isBootstrapping: boolean;
  workspace: PlannerWorkspaceState | null;
  workspaceError: string | null;
  latestText: string;
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
      { message: latestText },
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
