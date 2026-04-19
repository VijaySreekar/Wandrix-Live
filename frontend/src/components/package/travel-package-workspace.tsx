"use client";

import { useEffect, useState } from "react";
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

        const initialTripList = await listTrips(24, session.access_token);
        const bootResult = await createWorkspace(
          session.access_token,
          {
            selectedTripId,
            forceNewTrip: Boolean(newChatNonce),
            recentTrips: initialTripList.items,
          },
        );
        const recentTripItems = bootResult.didCreateTrip
          ? (await listTrips(24, session.access_token)).items
          : initialTripList.items;

        if (!cancelled) {
          setWorkspace(bootResult.workspace);
          setRecentTrips(recentTripItems);
        }
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
    forceNewTrip: boolean;
    recentTrips: TripListItemResponse[];
  },
): Promise<{
  workspace: PlannerWorkspaceState;
  didCreateTrip: boolean;
}> {
  let browserSession = await ensureBrowserSession(accessToken);

  if (options.selectedTripId) {
    const trip = await getTrip(options.selectedTripId, accessToken);
    const tripDraft = await getTripDraft(trip.trip_id, accessToken);

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
  }

  if (!options.forceNewTrip && options.recentTrips.length > 0) {
    const latestTrip = await getTrip(options.recentTrips[0].trip_id, accessToken);
    const latestTripDraft = await getTripDraft(latestTrip.trip_id, accessToken);

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
    );
    const tripDraft = await getTripDraft(trip.trip_id, accessToken);

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
    browserSession = await ensureBrowserSession(accessToken);

    const trip = await createTrip(
      { browser_session_id: browserSession.browser_session_id },
      accessToken,
    );
    const tripDraft = await getTripDraft(trip.trip_id, accessToken);

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
  );

  window.sessionStorage.setItem(
    BROWSER_SESSION_STORAGE_KEY,
    browserSession.browser_session_id,
  );

  return browserSession;
}
