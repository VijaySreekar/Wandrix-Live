"use client";

import { useEffect, useState, type Dispatch, type SetStateAction } from "react";
import { useSearchParams } from "next/navigation";

import { TravelPlannerAssistant } from "@/components/assistant/travel-planner-assistant";
import { ChatSidebar } from "@/components/chat/chat-sidebar";
import { TripBoardPreview } from "@/components/package/trip-board-preview";
import { createBrowserSession } from "@/lib/api/browser-sessions";
import { createTrip, getTrip, getTripDraft, listTrips } from "@/lib/api/trips";
import { createClient as createSupabaseBrowserClient } from "@/lib/supabase/client";
import type { BrowserSessionCreateResponse } from "@/types/browser-session";
import type { PlannerWorkspaceState } from "@/types/planner-workspace";
import type { TripListItemResponse } from "@/types/trip";


const BROWSER_SESSION_STORAGE_KEY = "wandrix.browser_session_id";
const CHAT_SIDEBAR_COLLAPSED_KEY = "wandrix.chat_sidebar_collapsed";
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
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(() => {
    if (typeof window === "undefined") {
      return false;
    }

    return window.localStorage.getItem(CHAT_SIDEBAR_COLLAPSED_KEY) === "true";
  });

  useEffect(() => {
    window.localStorage.setItem(
      CHAT_SIDEBAR_COLLAPSED_KEY,
      isSidebarCollapsed ? "true" : "false",
    );
  }, [isSidebarCollapsed]);

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
          setRecentTrips(initialTripList.items);
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
      currentTrips.map((trip) =>
        trip.trip_id === workspace?.trip.trip_id
          ? {
              ...trip,
              title: nextDraft.title,
              phase: nextDraft.status.phase,
            }
          : trip,
      ),
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
      const trip = await getTrip(preferredTripId, accessToken, options.signal);
      const tripDraft = await getTripDraft(trip.trip_id, accessToken, options.signal);

      return {
        workspace: {
          browserSession: {
            ...browserSession,
            browser_session_id: trip.browser_session_id,
          },
          trip,
          tripDraft,
        },
        didCreateTrip: false,
      };
    } catch (caughtError) {
      const shouldRecoverRememberedTrip =
        preferredTripId === options.rememberedTripId &&
        caughtError instanceof Error &&
        caughtError.message === "Trip was not found.";

      if (!shouldRecoverRememberedTrip) {
        throw caughtError;
      }

      window.localStorage.removeItem(LAST_ACTIVE_TRIP_STORAGE_KEY);
    }
  }

  if (!options.forceNewTrip && options.recentTrips.length > 0) {
    const latestTrip = await getTrip(
      options.recentTrips[0].trip_id,
      accessToken,
      options.signal,
    );
    const latestTripDraft = await getTripDraft(
      latestTrip.trip_id,
      accessToken,
      options.signal,
    );

    return {
      workspace: {
        browserSession: {
          ...browserSession,
          browser_session_id: latestTrip.browser_session_id,
        },
        trip: latestTrip,
        tripDraft: latestTripDraft,
      },
      didCreateTrip: false,
    };
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
