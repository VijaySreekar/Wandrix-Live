"use client";

import { useEffect, useRef, useState, type Dispatch, type SetStateAction } from "react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";

import { TravelPlannerAssistant } from "@/components/assistant/travel-planner-assistant";
import { ChatSidebar } from "@/components/chat/chat-sidebar";
import { useChatSidebarCollapsedState } from "@/components/chat/use-chat-sidebar-collapsed-state";
import { TripBoardPreview } from "@/components/package/trip-board-preview";
import { createBrowserSession } from "@/lib/api/browser-sessions";
import { createTrip, getTrip, getTripDraft, listTrips } from "@/lib/api/trips";
import {
  toBrowserAuthSnapshot,
  type BrowserAuthSnapshot,
} from "@/lib/supabase/auth-snapshot";
import {
  buildEphemeralWorkspace,
  buildStarterTripDraft,
} from "@/lib/trip-draft-starter";
import { createClient as createSupabaseBrowserClient } from "@/lib/supabase/client";
import {
  getRecentTripsCacheKey,
  readRecentTripsCache,
  writeRecentTripsCache,
} from "@/lib/recent-trips-cache";
import type { PlannerBoardActionIntent } from "@/types/planner-board";
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
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const selectedTripId = searchParams.get("trip");
  const [workspace, setWorkspace] = useState<PlannerWorkspaceState | null>(null);
  const [recentTrips, setRecentTrips] = useState<TripListItemResponse[]>([]);
  const [workspaceError, setWorkspaceError] = useState<string | null>(null);
  const [isBootstrapping, setIsBootstrapping] = useState(true);
  const [isCreatingTrip, setIsCreatingTrip] = useState(false);
  const [pendingBoardAction, setPendingBoardAction] =
    useState<PlannerBoardActionIntent | null>(null);
  const [recentTripsCacheKey, setRecentTripsCacheKey] = useState<string | null>(null);
  const [authSnapshot, setAuthSnapshot] = useState<BrowserAuthSnapshot | null>(null);
  const [pendingTripId, setPendingTripId] = useState<string | null>(null);
  const [freshTripIds, setFreshTripIds] = useState<string[]>([]);
  const activeTripId = pendingTripId ?? selectedTripId ?? workspace?.trip.trip_id ?? null;
  const workspaceTripIdRef = useRef<string | null>(null);
  const { isSidebarCollapsed, setIsSidebarCollapsed } =
    useChatSidebarCollapsedState();

  useEffect(() => {
    workspaceTripIdRef.current = workspace?.trip.trip_id ?? null;
  }, [workspace?.trip.trip_id]);

  useEffect(() => {
    let cancelled = false;

    async function bootstrapWorkspace() {
      if (!selectedTripId && pendingTripId && workspaceTripIdRef.current === pendingTripId) {
        setWorkspaceError(null);
        setIsBootstrapping(false);
        return;
      }

      if (!selectedTripId && workspace?.isEphemeral) {
        setWorkspaceError(null);
        setIsBootstrapping(false);
        return;
      }

      if (selectedTripId && workspaceTripIdRef.current === selectedTripId) {
        setWorkspaceError(null);
        setIsBootstrapping(false);
        return;
      }

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

        const nextAuthSnapshot = toBrowserAuthSnapshot(session);
        setAuthSnapshot(nextAuthSnapshot);

        if (!nextAuthSnapshot) {
          throw new Error("Sign in to start a persisted trip workspace.");
        }

        const cacheKey = getRecentTripsCacheKey(nextAuthSnapshot.userId);
        setRecentTripsCacheKey(cacheKey);

        const cachedTrips = readRecentTripsCache(cacheKey);
        if (!cancelled && cachedTrips.length > 0) {
          setRecentTrips(cachedTrips);
        }

        const rememberedTripId =
          selectedTripId ? null : readLastActiveTripId();
        const seedTrips =
          cachedTrips.length > 0
            ? cachedTrips
            : (await loadInitialTripList(nextAuthSnapshot.accessToken)).items;

        if (!cancelled) {
          setRecentTrips(seedTrips);
        }

        const bootResult = await withAbortableTimeout(
          (signal) =>
            createWorkspace(nextAuthSnapshot.accessToken, {
              selectedTripId,
              rememberedTripId,
              recentTrips: seedTrips,
              signal,
            }),
          WORKSPACE_BOOTSTRAP_TIMEOUT_MS,
          "Workspace setup took too long.",
        );

        if (!cancelled) {
          setWorkspace(bootResult.workspace);
          setRecentTrips(
            mergeRecentTripsWithWorkspace(
              seedTrips,
              bootResult.workspace,
            ),
          );
        }

        void refreshRecentTrips(
          nextAuthSnapshot.accessToken,
          () => cancelled,
          setRecentTrips,
        );
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
  }, [pendingTripId, selectedTripId, workspace?.isEphemeral]);

  useEffect(() => {
    if (!recentTripsCacheKey) {
      return;
    }

    writeRecentTripsCache(recentTripsCacheKey, recentTrips);
  }, [recentTrips, recentTripsCacheKey]);

  useEffect(() => {
    if (!workspace?.trip.trip_id || workspace.isEphemeral) {
      window.localStorage.removeItem(LAST_ACTIVE_TRIP_STORAGE_KEY);
      return;
    }

    window.localStorage.setItem(LAST_ACTIVE_TRIP_STORAGE_KEY, workspace.trip.trip_id);
  }, [workspace?.isEphemeral, workspace?.trip.trip_id]);

  function handleDraftUpdated(nextDraft: PlannerWorkspaceState["tripDraft"]) {
    setWorkspace((current) => {
      if (!current) {
        return current;
      }

      const nextWorkspace = {
        ...current,
        trip: {
          ...current.trip,
          title: nextDraft.title,
        },
        tripDraft: nextDraft,
      };

      setRecentTrips((currentTrips) =>
        nextWorkspace.isEphemeral
          ? currentTrips
          : mergeRecentTripsWithWorkspace(currentTrips, nextWorkspace),
      );

      return nextWorkspace;
    });
  }

  async function ensurePersistedTrip() {
    if (!workspace) {
      return null;
    }

    if (!workspace.isEphemeral) {
      return workspace;
    }

    const nextAuthSnapshot = await resolveWorkspaceAuthSnapshot(
      authSnapshot,
      setAuthSnapshot,
    );

    if (!nextAuthSnapshot) {
      throw new Error("Sign in to start a persisted trip workspace.");
    }

    let browserSession = workspace.browserSession;
    if (
      !browserSession.browser_session_id ||
      browserSession.browser_session_id.startsWith("draft_browser_session_")
    ) {
      browserSession = await ensureBrowserSession(nextAuthSnapshot.accessToken);
    }

    const trip = await createTrip(
      { browser_session_id: browserSession.browser_session_id },
      nextAuthSnapshot.accessToken,
    );
    const nextWorkspace: PlannerWorkspaceState = {
      isEphemeral: false,
      browserSession,
      trip,
      tripDraft: buildStarterTripDraft(trip),
    };

    return nextWorkspace;
  }

  function activatePersistedTrip(nextWorkspace: PlannerWorkspaceState) {
    setPendingTripId(nextWorkspace.trip.trip_id);
    setFreshTripIds((current) =>
      current.includes(nextWorkspace.trip.trip_id)
        ? current
        : [nextWorkspace.trip.trip_id, ...current],
    );
    setWorkspace(nextWorkspace);
    setRecentTrips((currentTrips) =>
      mergeRecentTripsWithWorkspace(currentTrips, nextWorkspace),
    );

    const nextParams = new URLSearchParams(searchParams.toString());
    nextParams.set("trip", nextWorkspace.trip.trip_id);
    nextParams.delete("new");
    const nextQuery = nextParams.toString();
    router.replace(nextQuery ? `${pathname}?${nextQuery}` : pathname, {
      scroll: false,
    });
  }

  async function handleCreateTrip() {
    if (isCreatingTrip) {
      return;
    }

    setIsCreatingTrip(true);
    setWorkspaceError(null);

    try {
      const nextParams = new URLSearchParams(searchParams.toString());
      nextParams.delete("trip");
      nextParams.delete("new");
      const nextQuery = nextParams.toString();
      const storedBrowserSessionId = window.sessionStorage.getItem(
        BROWSER_SESSION_STORAGE_KEY,
      );
      const nextWorkspace = buildEphemeralWorkspace(storedBrowserSessionId);

      setPendingTripId(null);
      setWorkspace(nextWorkspace);
      router.replace(
        nextQuery ? `${pathname}?${nextQuery}` : pathname,
        { scroll: false },
      );
    } catch (caughtError) {
      setPendingTripId(null);
      setWorkspaceError(
        caughtError instanceof Error
          ? caughtError.message
          : "Could not start a new trip.",
      );
    } finally {
      setIsCreatingTrip(false);
    }
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
        activeTripId={activeTripId}
        collapsed={isSidebarCollapsed}
        onSelectTrip={() => setPendingTripId(null)}
        onToggleCollapsed={() => setIsSidebarCollapsed((current) => !current)}
        onCreateTrip={handleCreateTrip}
        isCreatingTrip={isCreatingTrip}
        workspace={workspace}
        recentTrips={recentTrips}
      />

      <div className="min-h-0 border-r border-[color:var(--chat-rail-border)] bg-[color:var(--chat-pane-bg)]">
        <TravelPlannerAssistant
          activeTripId={activeTripId}
          authSnapshot={authSnapshot}
          skipInitialHistorySync={Boolean(
            (activeTripId && freshTripIds.includes(activeTripId)) ||
              workspace?.isEphemeral,
          )}
          onEnsurePersistedTrip={ensurePersistedTrip}
          onActivatePersistedTrip={activatePersistedTrip}
          workspace={workspace}
          isBootstrapping={isBootstrapping}
          workspaceError={workspaceError}
          pendingBoardAction={pendingBoardAction}
          onBoardActionHandled={(actionId) =>
            setPendingBoardAction((current) =>
              current?.action_id === actionId ? null : current,
            )
          }
          onDraftUpdated={handleDraftUpdated}
        />
      </div>

      <div className="min-h-0 bg-shell">
        <TripBoardPreview
          workspace={workspace}
          isBootstrapping={isBootstrapping || (Boolean(activeTripId) && workspace?.trip.trip_id !== activeTripId)}
          onAction={setPendingBoardAction}
        />
      </div>
    </section>
  );
}


async function resolveWorkspaceAuthSnapshot(
  currentSnapshot: BrowserAuthSnapshot | null,
  setAuthSnapshot: Dispatch<SetStateAction<BrowserAuthSnapshot | null>>,
) {
  if (currentSnapshot) {
    return currentSnapshot;
  }

  const supabase = createSupabaseBrowserClient();
  const {
    data: { session },
    error: sessionError,
  } = await supabase.auth.getSession();

  if (sessionError) {
    throw new Error("Could not read the Supabase session for this workspace.");
  }

  const nextSnapshot = toBrowserAuthSnapshot(session);
  setAuthSnapshot(nextSnapshot);
  return nextSnapshot;
}


async function createWorkspace(
  accessToken: string,
  options: {
    selectedTripId: string | null;
    rememberedTripId: string | null;
    recentTrips: TripListItemResponse[];
    signal: AbortSignal;
  },
): Promise<{
  workspace: PlannerWorkspaceState;
  didCreateTrip: boolean;
}> {
  let browserSession = await ensureBrowserSession(accessToken, options.signal);
  const preferredTripId =
    options.selectedTripId ?? options.rememberedTripId;

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

  if (options.recentTrips.length > 0) {
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
        isEphemeral: false,
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
        isEphemeral: false,
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
    isEphemeral: false,
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
  if (!storedTripId || !storedTripId.trim()) {
    return null;
  }

  return storedTripId.startsWith("draft_trip_") ? null : storedTripId;
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
