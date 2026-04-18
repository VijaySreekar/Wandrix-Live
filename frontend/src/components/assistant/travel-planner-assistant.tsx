"use client";

import { useMemo } from "react";

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
      <section className="flex h-full min-h-0 flex-col rounded-xl border border-shell-border bg-shell">
        <div className="flex flex-wrap items-center justify-between gap-4 border-b border-shell-border px-5 py-4">
          <div>
            <h2 className="text-base font-semibold text-foreground">Chat</h2>
            <p className="mt-1 text-sm text-foreground/68">
              {workspace
                ? `Connected to ${workspace.trip.trip_id} and ${workspace.trip.thread_id}.`
                : "Waiting for an authenticated trip workspace."}
            </p>
          </div>
          <div className="rounded-md border border-shell-border bg-panel px-3 py-2 text-xs font-medium text-foreground/65">
            {isBootstrapping ? "Booting" : "Backend bridge"}
          </div>
        </div>

        <ThreadPrimitive.Root className="flex min-h-0 flex-1 flex-col overflow-hidden">
          <ThreadPrimitive.Viewport className="flex min-h-0 flex-1 flex-col overflow-y-auto bg-panel-strong px-5 py-5">
            <ThreadPrimitive.Empty>
              <AssistantWelcome
                disabled={isBootstrapping}
                hasWorkspace={Boolean(workspace)}
                hasError={Boolean(workspaceError)}
              />
            </ThreadPrimitive.Empty>

            <div className="mt-auto flex flex-col gap-3">
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
    <div className="flex h-full min-h-[24rem] flex-col justify-between gap-6">
      <div className="space-y-4">
        <div className="space-y-2">
          <h3 className="text-3xl font-semibold tracking-tight text-foreground">
            Start planning through conversation.
          </h3>
          <p className="max-w-2xl text-sm leading-7 text-foreground/72">
            This assistant shell is now calling the FastAPI backend. The next
            layer is swapping the simple backend reply builder for the real
            LangGraph orchestration flow.
          </p>
        </div>

        <div className="rounded-lg border border-shell-border bg-shell px-4 py-4 text-sm leading-7 text-foreground/72">
          {disabled && <p>Finishing workspace setup before the first run.</p>}
          {!disabled && hasWorkspace && (
            <p>
              The runtime is ready. Messages now go through the authenticated
              backend trip conversation bridge.
            </p>
          )}
          {!disabled && !hasWorkspace && !hasError && (
            <p>Sign in first so the assistant can attach the conversation to a trip.</p>
          )}
          {!disabled && hasError && (
            <p>The workspace needs attention before the assistant can fully attach to it.</p>
          )}
        </div>
      </div>

      <div className="grid gap-3 sm:grid-cols-2">
        <ThreadPrimitive.Suggestion
          className="rounded-lg border border-shell-border bg-shell px-4 py-4 text-left text-sm leading-6 text-foreground transition-colors hover:bg-panel disabled:opacity-50"
          prompt="Plan a 5-day food and culture trip to Kyoto for two adults."
          autoSend
          disabled={disabled || !hasWorkspace}
        >
          Plan a 5-day food and culture trip to Kyoto for two adults.
        </ThreadPrimitive.Suggestion>
        <ThreadPrimitive.Suggestion
          className="rounded-lg border border-shell-border bg-shell px-4 py-4 text-left text-sm leading-6 text-foreground transition-colors hover:bg-panel disabled:opacity-50"
          prompt="Help me shape a luxury long weekend in Lisbon with flights and hotel ideas."
          autoSend
          disabled={disabled || !hasWorkspace}
        >
          Help me shape a luxury long weekend in Lisbon with flights and hotel ideas.
        </ThreadPrimitive.Suggestion>
        <ThreadPrimitive.Suggestion
          className="rounded-lg border border-shell-border bg-shell px-4 py-4 text-left text-sm leading-6 text-foreground transition-colors hover:bg-panel disabled:opacity-50"
          prompt="Suggest a relaxed family trip to Barcelona with weather-aware activities."
          autoSend
          disabled={disabled || !hasWorkspace}
        >
          Suggest a relaxed family trip to Barcelona with weather-aware activities.
        </ThreadPrimitive.Suggestion>
        <ThreadPrimitive.Suggestion
          className="rounded-lg border border-shell-border bg-shell px-4 py-4 text-left text-sm leading-6 text-foreground transition-colors hover:bg-panel disabled:opacity-50"
          prompt="What should the live trip board show as I refine my itinerary?"
          autoSend
          disabled={disabled}
        >
          What should the live trip board show as I refine my itinerary?
        </ThreadPrimitive.Suggestion>
      </div>
    </div>
  );
}

function UserMessage() {
  return (
    <MessagePrimitive.Root className="ml-auto max-w-[82%]">
      <div className="rounded-lg border border-accent/20 bg-accent-soft px-4 py-3 text-sm leading-7 text-foreground">
        <MessagePrimitive.Parts />
      </div>
    </MessagePrimitive.Root>
  );
}

function AssistantMessage() {
  return (
    <MessagePrimitive.Root className="max-w-[90%]">
      <div className="rounded-lg border border-shell-border bg-shell px-4 py-3 text-sm leading-7 text-foreground/85">
        <MessagePrimitive.Parts />
      </div>
    </MessagePrimitive.Root>
  );
}

function Composer() {
  return (
    <ComposerPrimitive.Root className="border-t border-shell-border bg-shell p-4">
      <div className="rounded-lg border border-shell-border bg-background px-3 py-3">
        <ComposerPrimitive.Input
          rows={1}
          placeholder="Describe the trip you want to build..."
          className="min-h-12 w-full resize-none bg-transparent text-sm leading-7 text-foreground outline-none placeholder:text-foreground/45"
        />
        <div className="mt-3 flex items-center justify-between gap-3">
          <p className="text-xs text-foreground/45">assistant-ui backend bridge</p>
          <ComposerPrimitive.Send asChild>
            <button
              type="button"
              className="rounded-md bg-accent px-4 py-2 text-sm font-semibold text-white transition-colors hover:bg-accent-strong"
            >
              Send
            </button>
          </ComposerPrimitive.Send>
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
