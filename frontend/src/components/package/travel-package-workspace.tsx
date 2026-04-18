"use client";

import { useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";

import { TravelPlannerAssistant } from "@/components/assistant/travel-planner-assistant";
import { ChatSidebar } from "@/components/chat/chat-sidebar";
import { PackageForm } from "@/components/package/package-form";
import { PackageResult } from "@/components/package/package-result";
import { TripBoardPreview } from "@/components/package/trip-board-preview";
import { createBrowserSession } from "@/lib/api/browser-sessions";
import { generateTravelPackage } from "@/lib/api/packages";
import { createTrip, getTrip, getTripDraft, listTrips } from "@/lib/api/trips";
import { createClient as createSupabaseBrowserClient } from "@/lib/supabase/client";
import type { BrowserSessionCreateResponse } from "@/types/browser-session";
import type { TravelPackageRequest, TravelPackageResponse } from "@/types/package";
import type { PlannerWorkspaceState } from "@/types/planner-workspace";
import type { TripListItemResponse } from "@/types/trip";


const BROWSER_SESSION_STORAGE_KEY = "wandrix.browser_session_id";


export function TravelPackageWorkspace() {
  const searchParams = useSearchParams();
  const newChatNonce = searchParams.get("new");
  const selectedTripId = searchParams.get("trip");
  const [workspace, setWorkspace] = useState<PlannerWorkspaceState | null>(null);
  const [recentTrips, setRecentTrips] = useState<TripListItemResponse[]>([]);
  const [workspaceError, setWorkspaceError] = useState<string | null>(null);
  const [isBootstrapping, setIsBootstrapping] = useState(true);
  const [lastDraftChanges, setLastDraftChanges] = useState<string[]>([]);
  const [result, setResult] = useState<TravelPackageResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    let cancelled = false;

    async function bootstrapWorkspace() {
      setWorkspace(null);
      setIsBootstrapping(true);
      setWorkspaceError(null);
      setLastDraftChanges([]);

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

        const bootData = await createWorkspace(
          session.access_token,
          selectedTripId,
        );
        const listedTrips = await listTrips(12, session.access_token);

        if (!cancelled) {
          setWorkspace(bootData);
          setRecentTrips(listedTrips.items);
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

  async function handleGenerate(payload: TravelPackageRequest) {
    setIsLoading(true);
    setError(null);

    try {
      const response = await generateTravelPackage(payload);
      setResult(response);
    } catch (caughtError) {
      setError(
        caughtError instanceof Error
          ? caughtError.message
          : "Something went wrong while generating the package.",
      );
    } finally {
      setIsLoading(false);
    }
  }

  function handleDraftUpdated(nextDraft: PlannerWorkspaceState["tripDraft"]) {
    setWorkspace((current) => {
      if (!current) {
        return current;
      }

      setLastDraftChanges(describeDraftChanges(current.tripDraft, nextDraft));

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
    <section className="grid h-full min-h-0 gap-3 xl:grid-cols-[260px_minmax(0,1.05fr)_minmax(0,0.95fr)]">
      <ChatSidebar workspace={workspace} recentTrips={recentTrips} />

      <div className="min-h-0">
        <TravelPlannerAssistant
          workspace={workspace}
          isBootstrapping={isBootstrapping}
          workspaceError={workspaceError}
          onDraftUpdated={handleDraftUpdated}
        />
      </div>

      <div className="min-h-0 space-y-3">
        <TripBoardPreview
          workspace={workspace}
          isBootstrapping={isBootstrapping}
          lastDraftChanges={lastDraftChanges}
        />

        <PackageFormPanel
          isBootstrapping={isBootstrapping}
          isLoading={isLoading}
          error={error}
          onGenerate={handleGenerate}
          result={result}
        />
      </div>
    </section>
  );
}


async function createWorkspace(
  accessToken: string,
  selectedTripId: string | null,
): Promise<PlannerWorkspaceState> {
  let browserSession = await ensureBrowserSession(accessToken);

  if (selectedTripId) {
    const trip = await getTrip(selectedTripId, accessToken);
    const tripDraft = await getTripDraft(trip.trip_id, accessToken);

    return {
      browserSession: {
        ...browserSession,
        browser_session_id: trip.browser_session_id,
      },
      trip,
      tripDraft,
    };
  }

  try {
    const trip = await createTrip(
      { browser_session_id: browserSession.browser_session_id },
      accessToken,
    );
    const tripDraft = await getTripDraft(trip.trip_id, accessToken);

    return {
      browserSession,
      trip,
      tripDraft,
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
      browserSession,
      trip,
      tripDraft,
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


function describeDraftChanges(
  previousDraft: PlannerWorkspaceState["tripDraft"],
  nextDraft: PlannerWorkspaceState["tripDraft"],
) {
  const changes: string[] = [];
  const previousConfig = previousDraft.configuration;
  const nextConfig = nextDraft.configuration;

  if (previousConfig.from_location !== nextConfig.from_location) {
    changes.push(`Origin set to ${nextConfig.from_location ?? "TBD"}.`);
  }

  if (previousConfig.to_location !== nextConfig.to_location) {
    changes.push(`Destination set to ${nextConfig.to_location ?? "TBD"}.`);
  }

  if (
    previousConfig.start_date !== nextConfig.start_date ||
    previousConfig.end_date !== nextConfig.end_date
  ) {
    changes.push(
      `Dates updated to ${nextConfig.start_date ?? "TBD"} through ${nextConfig.end_date ?? "TBD"}.`,
    );
  }

  if (previousConfig.budget_gbp !== nextConfig.budget_gbp) {
    changes.push(
      nextConfig.budget_gbp
        ? `Budget updated to GBP ${nextConfig.budget_gbp.toLocaleString()}.`
        : "Budget cleared.",
    );
  }

  if (
    previousConfig.travelers.adults !== nextConfig.travelers.adults ||
    previousConfig.travelers.children !== nextConfig.travelers.children
  ) {
    changes.push(
      `Traveler count is now ${nextConfig.travelers.adults} adults and ${nextConfig.travelers.children} children.`,
    );
  }

  if (previousDraft.status.phase !== nextDraft.status.phase) {
    changes.push(`Trip phase moved to ${nextDraft.status.phase}.`);
  }

  if (previousDraft.timeline.length !== nextDraft.timeline.length) {
    changes.push(`Timeline now has ${nextDraft.timeline.length} preview items.`);
  }

  const previousStyles = previousConfig.activity_styles.join("|");
  const nextStyles = nextConfig.activity_styles.join("|");
  if (previousStyles !== nextStyles && nextConfig.activity_styles.length > 0) {
    changes.push(`Activity styles now include ${nextConfig.activity_styles.join(", ")}.`);
  }

  const previousMissing = previousDraft.status.missing_fields.join("|");
  const nextMissing = nextDraft.status.missing_fields.join("|");
  if (previousMissing !== nextMissing) {
    if (nextDraft.status.missing_fields.length > 0) {
      changes.push(`Still missing ${nextDraft.status.missing_fields.join(", ")}.`);
    } else {
      changes.push("The draft now has the core fields needed for planning.");
    }
  }

  return changes.slice(0, 6);
}


function PackageFormPanel({
  isBootstrapping,
  isLoading,
  error,
  onGenerate,
  result,
}: {
  isBootstrapping: boolean;
  isLoading: boolean;
  error: string | null;
  onGenerate: (payload: TravelPackageRequest) => Promise<void>;
  result: TravelPackageResponse | null;
}) {
  return (
    <div className="space-y-3 rounded-xl border border-shell-border bg-shell p-4">
      <div className="rounded-lg border border-shell-border bg-panel px-5 py-4">
        <h2 className="mt-2 font-display text-3xl font-semibold tracking-tight text-foreground">
          Prompt the board directly
        </h2>
        <p className="mt-2 text-sm leading-7 text-foreground/75">
          This form stays here as a fast planner shortcut while the chat remains
          the main product experience.
        </p>
      </div>

      <div className="rounded-lg border border-shell-border bg-panel p-5">
        <PackageForm onSubmit={onGenerate} isLoading={isLoading || isBootstrapping} />
        {error && (
          <p className="mt-4 rounded-md border border-shell-border bg-background px-4 py-3 text-sm text-foreground/80">
            {error}
          </p>
        )}
      </div>

      <PackageResult result={result} />
    </div>
  );
}
