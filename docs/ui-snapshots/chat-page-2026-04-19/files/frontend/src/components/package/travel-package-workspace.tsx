"use client";

import { useEffect, useState, type Dispatch, type SetStateAction } from "react";
import { useSearchParams } from "next/navigation";

import { TravelPlannerAssistant } from "@/components/assistant/travel-planner-assistant";
import { ChatSidebar } from "@/components/chat/chat-sidebar";
import { useChatSidebarCollapsedState } from "@/components/chat/use-chat-sidebar-collapsed-state";
import { TripBoardPreview } from "@/components/package/trip-board-preview";
import { createBrowserSession } from "@/lib/api/browser-sessions";
import { createTrip, getTrip, getTripDraft, listTrips } from "@/lib/api/trips";
import { createClient as createSupabaseBrowserClient } from "@/lib/supabase/client";
import type { BrowserSessionCreateResponse } from "@/types/browser-session";
import type { PlannerWorkspaceState } from "@/types/planner-workspace";
import type { TripListItemResponse } from "@/types/trip";


const BROWSER_SESSION_STORAGE_KEY = "wandrix.browser_session_id";
const LAST_ACTIVE_TRIP_STORAGE_KEY = "wandrix.last_active_trip_id";
const RECENT_TRIPS_LIMIT = 24;
const TRIP_LIST_BOOTSTRAP_TIMEOUT_MS = 3500;
const RECENT_TRIPS_REFRESH_TIMEOUT_MS = 5000;
const WORKSPACE_BOOTSTRAP_TIMEOUT_MS = 12000;


export function TravelPackageWorkspace() {
  const searchParams = useSearchParams();
  const newChatNonce = searchParams.get("new");
  const selectedTripId = searchParams.get("trip");
  const [workspace, setWorkspace] = useState<PlannerWorkspaceState | null>(null);
  const [recentTrips, setRecentTrips] = useState<TripListItemResponse[]>([]);
  const [workspaceError, setWorkspaceError] = useState<string | null>(null);
  const [isBootstrapping, setIsBootstrapping] = useState(true);
  const { isSidebarCollapsed, setIsSidebarCollapsed } =
    useChatSidebarCollapsedState();

  useEffect(() => {
    let cancelled = false;

    async function bootstrapWorkspace() {
      setWorkspace(null);
      setIsBootstrapping(true);
      setWorkspaceError(null);

      try {
        const supabase = createSupabaseBrowserClient();
        const {
          data: { session },
          error: sessionError,
        } = await supabase.auth.getSession();

        if (sessionError) {
          throw new Error("Could not read the Supabase session for this workspace.");
        }

        if (!session?.access_token) {
          throw new Error("Sign in to start a persisted trip workspace.");
        }

        const rememberedTripId =
          newChatNonce || selectedTripId ? null : readLastActiveTripId();
        const forceNewTrip = Boolean(newChatNonce);
        const initialTripList = forceNewTrip
          ? { items: [] }
          : await loadInitialTripList(session.access_token);

        if (!cancelled) {
          setRecentTrips(initialTripList.items);
        }

        const bootResult = await withAbortableTimeout(
          (signal) =>
            createWorkspace(session.access_token, {
              selectedTripId,
              rememberedTripId,
              forceNewTrip,
              recentTrips: initialTripList.items,
              signal,
            }),
          WORKSPACE_BOOTSTRAP_TIMEOUT_MS,
          "Workspace setup took too long.",
        );

        if (!cancelled) {
          setWorkspace(bootResult.workspace);
          setRecentTrips(
            mergeRecentTripsWithWorkspace(
              initialTripList.items,
              bootResult.workspace,
            ),
          );
        }

        void refreshRecentTrips(session.access_token, () => cancelled, setRecentTrips);
      } catch (caughtError) {
        if (!cancelled) {
          setWorkspaceError(
            caughtError instanceof Error
              ? caughtError.message
              : "Could not start the trip workspace.",
          );
        }
      } finally {
        if (!cancelled) {
          setIsBootstrapping(false);
        }
      }
    }

    void bootstrapWorkspace();

    return () => {
      cancelled = true;
    };
  }, [newChatNonce, selectedTripId]);

  useEffect(() => {
    if (!workspace?.trip.trip_id) {
      window.localStorage.removeItem(LAST_ACTIVE_TRIP_STORAGE_KEY);
      return;
    }

    window.localStorage.setItem(LAST_ACTIVE_TRIP_STORAGE_KEY, workspace.trip.trip_id);
  }, [workspace?.trip.trip_id]);

  function handleDraftUpdated(nextDraft: PlannerWorkspaceState["tripDraft"]) {
    setWorkspace((current) => {
      if (!current) {
        return current;
      }

      return {
        ...current,
        tripDraft: nextDraft,
      };
    });

    setRecentTrips((currentTrips) =>
      workspace
        ? mergeRecentTripsWithWorkspace(currentTrips, {
            ...workspace,
            tripDraft: nextDraft,
          })
        : currentTrips,
    );
  }

  return (
    <section
      className={[
        "grid h-full min-h-0 bg-background",
        isSidebarCollapsed
          ? "xl:grid-cols-[72px_minmax(0,0.72fr)_minmax(0,1.28fr)]"
          : "xl:grid-cols-[264px_minmax(0,0.8fr)_minmax(0,1.2fr)]",
      ].join(" ")}
    >
      <ChatSidebar
        collapsed={isSidebarCollapsed}
        onToggleCollapsed={() => setIsSidebarCollapsed((current) => !current)}
        workspace={workspace}
        recentTrips={recentTrips}
      />

      <div className="min-h-0 border-r border-[color:var(--chat-rail-border)] bg-[color:var(--chat-pane-bg)]">
        <TravelPlannerAssistant
          workspace={workspace}
          isBootstrapping={isBootstrapping}
          workspaceError={workspaceError}
          onDraftUpdated={handleDraftUpdated}
        />
      </div>

      <div className="min-h-0 bg-shell">
        <TripBoardPreview
          workspace={workspace}
          isBootstrapping={isBootstrapping}
        />
      </div>
    </section>
  );
}


async function createWorkspace(
  accessToken: string,
  options: {
    selectedTripId: string | null;
    rememberedTripId: string | null;
    forceNewTrip: boolean;
    recentTrips: TripListItemResponse[];
    signal: AbortSignal;
  },
): Promise<{
  workspace: PlannerWorkspaceState;
  didCreateTrip: boolean;
}> {
  let browserSession = await ensureBrowserSession(accessToken, options.signal);
  const preferredTripId =
    options.selectedTripId ?? (!options.forceNewTrip ? options.rememberedTripId : null);

  if (preferredTripId) {
    try {
      return {
        workspace: await loadWorkspaceForTrip(
          preferredTripId,
          accessToken,
          browserSession,
          options.signal,
        ),
        didCreateTrip: false,
      };
    } catch (caughtError) {
      const shouldRecoverRememberedTrip =
        preferredTripId === options.rememberedTripId &&
        caughtError instanceof Error &&
        caughtError.message === "Trip was not found.";

      if (!shouldRecoverRememberedTrip) {
        if (options.selectedTripId) {
          throw caughtError;
        }
      }

      if (preferredTripId === options.rememberedTripId) {
        window.localStorage.removeItem(LAST_ACTIVE_TRIP_STORAGE_KEY);
      }
    }
  }

  if (!options.forceNewTrip && options.recentTrips.length > 0) {
    for (const recentTrip of options.recentTrips) {
      if (recentTrip.trip_id === preferredTripId) {
        continue;
      }

      try {
        return {
          workspace: await loadWorkspaceForTrip(
            recentTrip.trip_id,
            accessToken,
            browserSession,
            options.signal,
          ),
          didCreateTrip: false,
        };
      } catch {
        // Skip broken auto-selected trips and keep trying older saved sessions.
      }
    }
  }

  try {
    const trip = await createTrip(
      { browser_session_id: browserSession.browser_session_id },
      accessToken,
      options.signal,
    );
    const tripDraft = await getTripDraft(trip.trip_id, accessToken, options.signal);

    return {
      workspace: {
        browserSession,
        trip,
        tripDraft,
      },
      didCreateTrip: true,
    };
  } catch (caughtError) {
    const shouldRecover =
      caughtError instanceof Error &&
      caughtError.message === "Browser session was not found.";

    if (!shouldRecover) {
      throw caughtError;
    }

    window.sessionStorage.removeItem(BROWSER_SESSION_STORAGE_KEY);
    browserSession = await ensureBrowserSession(accessToken, options.signal);

    const trip = await createTrip(
      { browser_session_id: browserSession.browser_session_id },
      accessToken,
      options.signal,
    );
    const tripDraft = await getTripDraft(trip.trip_id, accessToken, options.signal);

    return {
      workspace: {
        browserSession,
        trip,
        tripDraft,
      },
      didCreateTrip: true,
    };
  }
}

async function loadWorkspaceForTrip(
  tripId: string,
  accessToken: string,
  browserSession: BrowserSessionCreateResponse,
  signal: AbortSignal,
): Promise<PlannerWorkspaceState> {
  const trip = await getTrip(tripId, accessToken, signal);
  const tripDraft = await getTripDraft(trip.trip_id, accessToken, signal);

  return {
    browserSession: {
      ...browserSession,
      browser_session_id: trip.browser_session_id,
    },
    trip,
    tripDraft,
  };
}


async function ensureBrowserSession(
  accessToken: string,
  signal?: AbortSignal,
): Promise<BrowserSessionCreateResponse> {
  const storedBrowserSessionId = window.sessionStorage.getItem(BROWSER_SESSION_STORAGE_KEY);

  if (storedBrowserSessionId) {
    return {
      browser_session_id: storedBrowserSessionId,
      user_id: null,
      timezone: null,
      locale: null,
      status: "active",
      created_at: "",
    };
  }

  const browserSession = await createBrowserSession(
    {
      timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
      locale: navigator.language,
    },
    accessToken,
    signal,
  );

  window.sessionStorage.setItem(
    BROWSER_SESSION_STORAGE_KEY,
    browserSession.browser_session_id,
  );

  return browserSession;
}

async function loadInitialTripList(accessToken: string) {
  try {
    return await withAbortableTimeout(
      (signal) => listTrips(RECENT_TRIPS_LIMIT, accessToken, signal),
      TRIP_LIST_BOOTSTRAP_TIMEOUT_MS,
      "Timed out while loading saved trips.",
    );
  } catch {
    return { items: [] };
  }
}

async function refreshRecentTrips(
  accessToken: string,
  shouldCancel: () => boolean,
  setRecentTrips: Dispatch<SetStateAction<TripListItemResponse[]>>,
) {
  try {
    const nextTrips = await withAbortableTimeout(
      (signal) => listTrips(RECENT_TRIPS_LIMIT, accessToken, signal),
      RECENT_TRIPS_REFRESH_TIMEOUT_MS,
      "Timed out while refreshing saved trips.",
    );

    if (!shouldCancel()) {
      setRecentTrips(nextTrips.items);
    }
  } catch {
    // Keep the current workspace responsive even if the sidebar list refresh fails.
  }
}

function readLastActiveTripId() {
  const storedTripId = window.localStorage.getItem(LAST_ACTIVE_TRIP_STORAGE_KEY);
  return storedTripId && storedTripId.trim() ? storedTripId : null;
}

function mergeRecentTripsWithWorkspace(
  recentTrips: TripListItemResponse[],
  workspace: PlannerWorkspaceState,
) {
  const currentTrip = buildRecentTripItem(workspace);

  return [
    currentTrip,
    ...recentTrips.filter((trip) => trip.trip_id !== currentTrip.trip_id),
  ];
}

function buildRecentTripItem(
  workspace: PlannerWorkspaceState,
): TripListItemResponse {
  const selectedModules = Object.entries(
    workspace.tripDraft.configuration.selected_modules,
  )
    .filter(([, enabled]) => enabled)
    .map(([moduleName]) => moduleName);

  return {
    trip_id: workspace.trip.trip_id,
    browser_session_id: workspace.trip.browser_session_id,
    thread_id: workspace.trip.thread_id,
    title: workspace.tripDraft.title,
    trip_status: workspace.trip.trip_status,
    thread_status: workspace.trip.thread_status,
    created_at: workspace.trip.created_at,
    updated_at:
      workspace.tripDraft.status.last_updated_at ?? workspace.trip.created_at,
    phase: workspace.tripDraft.status.phase,
    brochure_ready: workspace.tripDraft.status.brochure_ready,
    from_location: workspace.tripDraft.configuration.from_location,
    to_location: workspace.tripDraft.configuration.to_location,
    start_date: workspace.tripDraft.configuration.start_date,
    end_date: workspace.tripDraft.configuration.end_date,
    travel_window: workspace.tripDraft.configuration.travel_window,
    trip_length: workspace.tripDraft.configuration.trip_length,
    selected_modules: selectedModules,
    timeline_item_count: workspace.tripDraft.timeline.length,
  };
}

async function withAbortableTimeout<T>(
  run: (signal: AbortSignal) => Promise<T>,
  timeoutMs: number,
  timeoutMessage: string,
): Promise<T> {
  const controller = new AbortController();

  return await new Promise<T>((resolve, reject) => {
    const timeout = window.setTimeout(() => {
      controller.abort(new DOMException(timeoutMessage, "AbortError"));
      reject(new Error(timeoutMessage));
    }, timeoutMs);

    run(controller.signal)
      .then((value) => {
        window.clearTimeout(timeout);
        resolve(value);
      })
      .catch((error: unknown) => {
        window.clearTimeout(timeout);
        if (
          (error instanceof DOMException && error.name === "AbortError") ||
          (error instanceof Error && error.name === "AbortError")
        ) {
          reject(new Error(timeoutMessage));
          return;
        }

        reject(error);
      });
  });
}
