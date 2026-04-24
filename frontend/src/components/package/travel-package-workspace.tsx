"use client";

import {
  useEffect,
  useRef,
  useState,
  type Dispatch,
  type SetStateAction,
} from "react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";

import { TravelPlannerAssistant } from "@/components/assistant/travel-planner-assistant";
import { ChatSidebar } from "@/components/chat/chat-sidebar";
import { useChatSidebarCollapsedState } from "@/components/chat/use-chat-sidebar-collapsed-state";
import { TripBoardPreview } from "@/components/package/trip-board-preview";
import { getTripConversationHistory } from "@/lib/api/conversation";
import { createBrowserSession } from "@/lib/api/browser-sessions";
import {
  createTrip,
  deleteTrip,
  getTrip,
  getTripDraft,
  listTrips,
  saveTripDraft,
} from "@/lib/api/trips";
import {
  normalizeHistoryMessages,
  readCachedThreadMessages,
  removeCachedThreadMessages,
  writeCachedThreadMessages,
} from "@/lib/chat-history-cache";
import {
  toBrowserAuthSnapshot,
  type BrowserAuthSnapshot,
} from "@/lib/supabase/auth-snapshot";
import {
  buildEphemeralWorkspace,
  buildStarterTripDraft,
  isEphemeralTripId,
} from "@/lib/trip-draft-starter";
import { createClient as createSupabaseBrowserClient } from "@/lib/supabase/client";
import {
  filterMeaningfulRecentTrips,
  getRecentTripsCacheKey,
  mergeRecentTripsForSidebarRefresh,
  readRecentTripsCache,
  sortRecentTripsByActivity,
  writeRecentTripsCache,
} from "@/lib/recent-trips-cache";
import type { PlannerBoardActionIntent } from "@/types/planner-board";
import type { BrowserSessionCreateResponse } from "@/types/browser-session";
import type { PlannerWorkspaceState } from "@/types/planner-workspace";
import type { TripListItemResponse } from "@/types/trip";


const BROWSER_SESSION_STORAGE_KEY = "wandrix.browser_session_id";
const LAST_ACTIVE_TRIP_STORAGE_KEY = "wandrix.last_active_trip_id";
const RECENT_TRIPS_LIMIT = 24;
const TRIP_LIST_BOOTSTRAP_TIMEOUT_MS = 15000;
const RECENT_TRIPS_REFRESH_TIMEOUT_MS = 15000;
const WORKSPACE_BOOTSTRAP_TIMEOUT_MS = 12000;
const CHAT_ROUTE = "/chat";
const NEW_CHAT_ROUTE = "/chat/new";
const WORKSPACE_CACHE_PREFIX = "wandrix:workspace-cache:";

export function TravelPackageWorkspace({
  initialMode = "default",
}: {
  initialMode?: "default" | "new";
}) {
  const [supabase] = useState(() => createSupabaseBrowserClient());
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const rawSelectedTripId = searchParams.get("trip");
  const routeSelectedTripId = isEphemeralTripId(rawSelectedTripId)
    ? null
    : rawSelectedTripId;
  const [clientSelectedTripId, setClientSelectedTripId] =
    useState<string | null | undefined>(undefined);
  const selectedTripId =
    clientSelectedTripId === undefined ? routeSelectedTripId : clientSelectedTripId;
  const [initialWorkspace] = useState<PlannerWorkspaceState | null>(() =>
    initialMode === "new"
      ? buildEphemeralWorkspace(null)
      : readInitialWorkspace(routeSelectedTripId),
  );
  const [workspace, setWorkspace] =
    useState<PlannerWorkspaceState | null>(initialWorkspace);
  const [recentTrips, setRecentTrips] = useState<TripListItemResponse[]>([]);
  const [workspaceError, setWorkspaceError] = useState<string | null>(null);
  const [isBootstrapping, setIsBootstrapping] = useState(
    !initialWorkspace && initialMode !== "new",
  );
  const [isCreatingTrip, setIsCreatingTrip] = useState(false);
  const [deletingTripId, setDeletingTripId] = useState<string | null>(null);
  const [renamingTripId, setRenamingTripId] = useState<string | null>(null);
  const [pendingBoardAction, setPendingBoardAction] =
    useState<PlannerBoardActionIntent | null>(null);
  const [recentTripsCacheKey, setRecentTripsCacheKey] = useState<string | null>(null);
  const [authSnapshot, setAuthSnapshot] = useState<BrowserAuthSnapshot | null>(null);
  const [pendingTripId, setPendingTripId] = useState<string | null>(null);
  const [freshTripIds, setFreshTripIds] = useState<string[]>([]);
  const requestedTripId =
    pendingTripId ?? selectedTripId ?? workspace?.trip.trip_id ?? null;
  const displayedTripId = workspace?.trip.trip_id ?? null;
  const isSwitchingTrips = Boolean(
    requestedTripId &&
      displayedTripId &&
      requestedTripId !== displayedTripId,
  );
  const recentTripsRef = useRef<TripListItemResponse[]>([]);
  const workspaceTripIdRef = useRef<string | null>(null);
  const detachedPersistedWorkspaceRef = useRef<PlannerWorkspaceState | null>(null);
  const prefetchedWorkspaceRef = useRef(new Map<string, PlannerWorkspaceState>());
  const tripPrefetchPromiseRef = useRef(new Map<string, Promise<void>>());
  const recentTripsRefreshKeyRef = useRef<string | null>(null);
  const sparseRecentTripsRefreshKeyRef = useRef<string | null>(null);
  const { isSidebarCollapsed, setIsSidebarCollapsed } =
    useChatSidebarCollapsedState();
  const shouldOpenFreshChat = initialMode === "new" && !selectedTripId;

  useEffect(() => {
    function handlePopState() {
      const nextTripId = new URLSearchParams(window.location.search).get("trip");
      setClientSelectedTripId(
        nextTripId && !isEphemeralTripId(nextTripId) ? nextTripId : null,
      );
    }

    window.addEventListener("popstate", handlePopState);
    return () => {
      window.removeEventListener("popstate", handlePopState);
    };
  }, []);

  useEffect(() => {
    void resolveWorkspaceAuthSnapshot(supabase, setAuthSnapshot);

    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange((_event, session) => {
      setAuthSnapshot((current) => {
        const nextSnapshot = toBrowserAuthSnapshot(session);

        if (
          current?.accessToken === nextSnapshot?.accessToken &&
          current?.userId === nextSnapshot?.userId
        ) {
          return current;
        }

        return nextSnapshot;
      });
    });

    return () => {
      subscription.unsubscribe();
    };
  }, [supabase]);

  useEffect(() => {
    recentTripsRef.current = recentTrips;
  }, [recentTrips]);

  useEffect(() => {
    workspaceTripIdRef.current = workspace?.trip.trip_id ?? null;
  }, [workspace?.trip.trip_id]);

  useEffect(() => {
    if (!workspace || workspace.isEphemeral) {
      return;
    }

    writeWorkspaceCache(workspace);
  }, [workspace]);

  useEffect(() => {
    if (!workspace?.isEphemeral) {
      detachedPersistedWorkspaceRef.current = null;
    }
  }, [workspace?.isEphemeral, workspace?.trip.trip_id]);

  useEffect(() => {
    if (!rawSelectedTripId || !isEphemeralTripId(rawSelectedTripId)) {
      return;
    }

    const nextParams = new URLSearchParams(searchParams.toString());
    nextParams.delete("trip");
    const nextQuery = nextParams.toString();
    router.replace(nextQuery ? `${pathname}?${nextQuery}` : pathname, {
      scroll: false,
    });
  }, [pathname, rawSelectedTripId, router, searchParams]);

  useEffect(() => {
    let cancelled = false;

    async function bootstrapWorkspace() {
      const keepCurrentEphemeralWorkspace =
        !selectedTripId && workspace?.isEphemeral;
      const displayedRequestedWorkspace =
        Boolean(workspaceTripIdRef.current) &&
        ((!selectedTripId &&
          pendingTripId &&
          workspaceTripIdRef.current === pendingTripId) ||
          Boolean(selectedTripId && workspaceTripIdRef.current === selectedTripId));
      const hasRecentTrips =
        filterMeaningfulRecentTrips(recentTripsRef.current).length > 0;

      if (displayedRequestedWorkspace && !selectedTripId && pendingTripId) {
        setWorkspaceError(null);
        setPendingTripId((current) => (current === pendingTripId ? null : current));
        setIsBootstrapping(false);

        if (hasRecentTrips) {
          return;
        }
      }

      if (displayedRequestedWorkspace && selectedTripId) {
        setWorkspaceError(null);
        setPendingTripId((current) => (current === selectedTripId ? null : current));
        setIsBootstrapping(false);

        if (hasRecentTrips) {
          return;
        }
      }

      const rememberedTripId =
        shouldOpenFreshChat || selectedTripId ? null : readLastActiveTripId();
      const cachedWorkspace = readWorkspaceCache(
        pendingTripId ?? selectedTripId ?? rememberedTripId,
      );
      const canUseCachedWorkspace =
        Boolean(cachedWorkspace) &&
        !keepCurrentEphemeralWorkspace &&
        workspaceTripIdRef.current !== cachedWorkspace?.trip.trip_id;

      if (canUseCachedWorkspace && cachedWorkspace) {
        setWorkspace(cachedWorkspace);
        setRecentTrips((currentTrips) =>
          mergeRecentTripsWithWorkspace(currentTrips, cachedWorkspace),
        );
        setIsBootstrapping(false);
      }

      if (
        !displayedRequestedWorkspace &&
        !keepCurrentEphemeralWorkspace &&
        !canUseCachedWorkspace
      ) {
        setIsBootstrapping(true);
      }
      setWorkspaceError(null);

      try {
        const nextAuthSnapshot = await resolveWorkspaceAuthSnapshot(
          supabase,
          setAuthSnapshot,
        );

        if (!nextAuthSnapshot) {
          throw new Error("Sign in to start a persisted trip workspace.");
        }

        const cacheKey = getRecentTripsCacheKey(nextAuthSnapshot.userId);
        setRecentTripsCacheKey(cacheKey);

        const currentRecentTrips = filterMeaningfulRecentTrips(recentTripsRef.current);
        const cachedTrips =
          currentRecentTrips.length > 0
            ? currentRecentTrips
            : sortRecentTripsByActivity(
                filterMeaningfulRecentTrips(readRecentTripsCache(cacheKey)),
              );

        if (!cancelled && currentRecentTrips.length === 0 && cachedTrips.length > 0) {
          setRecentTrips(cachedTrips);
        }

        const seedTrips =
          selectedTripId
            ? cachedTrips
            : cachedTrips.length > 0
            ? cachedTrips
            : (await loadInitialTripList(nextAuthSnapshot.accessToken)).items;

        if (!cancelled && currentRecentTrips.length === 0) {
          setRecentTrips(seedTrips);
        }

        if (displayedRequestedWorkspace) {
          setWorkspaceError(null);

          if (
            shouldRefreshRecentTrips(
              cacheKey,
              recentTripsRefreshKeyRef.current,
              recentTripsRef.current,
            )
          ) {
            recentTripsRefreshKeyRef.current = cacheKey;
            void refreshRecentTrips(
              nextAuthSnapshot.accessToken,
              () => cancelled,
              setRecentTrips,
            );
          }

          return;
        }

        if (keepCurrentEphemeralWorkspace) {
          setWorkspaceError(null);

          if (
            shouldRefreshRecentTrips(
              cacheKey,
              recentTripsRefreshKeyRef.current,
              recentTripsRef.current,
            )
          ) {
            recentTripsRefreshKeyRef.current = cacheKey;
            void refreshRecentTrips(
              nextAuthSnapshot.accessToken,
              () => cancelled,
              setRecentTrips,
            );
          }

          return;
        }

        const bootResult = await withAbortableTimeout(
          (signal) =>
            createWorkspace({
              forceNewChat: shouldOpenFreshChat,
              selectedTripId,
              rememberedTripId,
              recentTrips: seedTrips,
              loadTripWorkspace: (tripId, tripSignal) =>
                loadTripWorkspaceWithPrefetch(
                  tripId,
                  nextAuthSnapshot.accessToken,
                  tripSignal,
                  prefetchedWorkspaceRef.current,
                ),
              signal,
            }),
          WORKSPACE_BOOTSTRAP_TIMEOUT_MS,
          "Workspace setup took too long.",
        );

        if (!cancelled) {
          setWorkspace(bootResult.workspace);
          setPendingTripId((current) =>
            current === bootResult.workspace.trip.trip_id ? null : current,
          );
          setRecentTrips(
            mergeRecentTripsWithWorkspace(
              currentRecentTrips.length > 0 ? currentRecentTrips : seedTrips,
              bootResult.workspace,
            ),
          );
        }

        if (
          shouldRefreshRecentTrips(
            cacheKey,
            recentTripsRefreshKeyRef.current,
            recentTripsRef.current,
          )
        ) {
          recentTripsRefreshKeyRef.current = cacheKey;
          void refreshRecentTrips(
            nextAuthSnapshot.accessToken,
            () => cancelled,
            setRecentTrips,
          );
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
  }, [
    pendingTripId,
    selectedTripId,
    shouldOpenFreshChat,
    supabase,
    workspace?.isEphemeral,
  ]);

  useEffect(() => {
    if (!recentTripsCacheKey) {
      return;
    }

    writeRecentTripsCache(recentTripsCacheKey, recentTrips);
  }, [recentTrips, recentTripsCacheKey]);

  useEffect(() => {
    if (!authSnapshot?.accessToken || !recentTripsCacheKey || !workspace?.trip.trip_id) {
      return;
    }

    if (filterMeaningfulRecentTrips(recentTrips).length > 1) {
      sparseRecentTripsRefreshKeyRef.current = null;
      return;
    }

    const refreshKey = `${recentTripsCacheKey}:${workspace.trip.trip_id}`;
    if (sparseRecentTripsRefreshKeyRef.current === refreshKey) {
      return;
    }

    sparseRecentTripsRefreshKeyRef.current = refreshKey;
    void refreshRecentTrips(
      authSnapshot.accessToken,
      () => false,
      setRecentTrips,
    );
  }, [
    authSnapshot?.accessToken,
    recentTrips,
    recentTripsCacheKey,
    workspace?.trip.trip_id,
  ]);

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

  async function handlePrefetchTrip(tripId: string) {
    if (
      !tripId ||
      tripId === selectedTripId ||
      tripId === requestedTripId ||
      tripId === workspaceTripIdRef.current ||
      prefetchedWorkspaceRef.current.has(tripId)
    ) {
      return;
    }

    const existingPrefetch = tripPrefetchPromiseRef.current.get(tripId);
    if (existingPrefetch) {
      return;
    }

    const nextPrefetch = (async () => {
      try {
        const nextAuthSnapshot = await resolveWorkspaceAuthSnapshot(
          supabase,
          setAuthSnapshot,
        );

        if (!nextAuthSnapshot) {
          return;
        }

        const historyAlreadyCached = readCachedThreadMessages(tripId).length > 0;
        const [workspaceResult, historyResult] = await Promise.allSettled([
          loadWorkspaceForTrip(tripId, nextAuthSnapshot.accessToken),
          historyAlreadyCached
            ? Promise.resolve(null)
            : getTripConversationHistory(tripId, nextAuthSnapshot.accessToken),
        ]);

        if (workspaceResult.status === "fulfilled") {
          prefetchedWorkspaceRef.current.set(tripId, workspaceResult.value);
        }

        if (
          historyResult.status === "fulfilled" &&
          historyResult.value
        ) {
          writeCachedThreadMessages(
            tripId,
            normalizeHistoryMessages(historyResult.value.messages),
          );
        }
      } catch {
        // Keep sidebar interactions quiet even if a background warm-up request fails.
      } finally {
        tripPrefetchPromiseRef.current.delete(tripId);
      }
    })();

    tripPrefetchPromiseRef.current.set(tripId, nextPrefetch);
    await nextPrefetch;
  }

  async function refreshSelectedTripWorkspace(tripId: string) {
    try {
      const nextAuthSnapshot = await resolveWorkspaceAuthSnapshot(
        supabase,
        setAuthSnapshot,
      );
      if (!nextAuthSnapshot) {
        return;
      }

      const nextWorkspace = await loadWorkspaceForTrip(
        tripId,
        nextAuthSnapshot.accessToken,
      );
      const currentUrlTripId = new URLSearchParams(window.location.search).get("trip");
      if (
        workspaceTripIdRef.current !== tripId &&
        currentUrlTripId !== tripId
      ) {
        return;
      }

      setWorkspace(nextWorkspace);
      setRecentTrips((currentTrips) =>
        mergeRecentTripsWithWorkspace(currentTrips, nextWorkspace),
      );
    } catch {
      // Cached workspace state is good enough for continuity; the next explicit refresh can recover.
    }
  }

  async function handleSelectTrip(tripId: string) {
    if (
      !tripId ||
      tripId === selectedTripId ||
      tripId === workspaceTripIdRef.current
    ) {
      return;
    }

    setWorkspaceError(null);

    const cachedWorkspace =
      prefetchedWorkspaceRef.current.get(tripId) ?? readWorkspaceCache(tripId);
    if (cachedWorkspace) {
      prefetchedWorkspaceRef.current.delete(tripId);
      setPendingTripId(tripId);
      setWorkspace(cachedWorkspace);
      setRecentTrips((currentTrips) =>
        mergeRecentTripsWithWorkspace(currentTrips, cachedWorkspace),
      );
      updateTripUrlWithoutNavigation(tripId);
      setClientSelectedTripId(tripId);
      void refreshSelectedTripWorkspace(tripId);
      return;
    }

    try {
      const nextAuthSnapshot = await resolveWorkspaceAuthSnapshot(
        supabase,
        setAuthSnapshot,
      );
      if (!nextAuthSnapshot) {
        throw new Error("Sign in to open this trip.");
      }

      const nextWorkspace = await loadWorkspaceForTrip(
        tripId,
        nextAuthSnapshot.accessToken,
      );
      setPendingTripId(tripId);
      setWorkspace(nextWorkspace);
      setRecentTrips((currentTrips) =>
        mergeRecentTripsWithWorkspace(currentTrips, nextWorkspace),
      );
      updateTripUrlWithoutNavigation(tripId);
      setClientSelectedTripId(tripId);
    } catch (caughtError) {
      setPendingTripId(null);
      setWorkspaceError(
        caughtError instanceof Error
          ? caughtError.message
          : "Could not open this trip.",
      );
    }
  }

  async function ensurePersistedTrip() {
    if (!workspace) {
      return null;
    }

    if (!workspace.isEphemeral) {
      return workspace;
    }

    if (detachedPersistedWorkspaceRef.current) {
      return detachedPersistedWorkspaceRef.current;
    }

    const nextAuthSnapshot = await resolveWorkspaceAuthSnapshot(
      supabase,
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

    detachedPersistedWorkspaceRef.current = nextWorkspace;
    return nextWorkspace;
  }

  function activatePersistedTrip(nextWorkspace: PlannerWorkspaceState) {
    detachedPersistedWorkspaceRef.current = null;
    setPendingTripId(nextWorkspace.trip.trip_id);
    setClientSelectedTripId(nextWorkspace.trip.trip_id);
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
    router.replace(nextQuery ? `${CHAT_ROUTE}?${nextQuery}` : CHAT_ROUTE, {
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
      const storedBrowserSessionId = window.sessionStorage.getItem(
        BROWSER_SESSION_STORAGE_KEY,
      );
      const nextWorkspace = buildEphemeralWorkspace(storedBrowserSessionId);

      detachedPersistedWorkspaceRef.current = null;
      setPendingTripId(null);
      setClientSelectedTripId(null);
      setWorkspace(nextWorkspace);
      router.replace(NEW_CHAT_ROUTE, { scroll: false });
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

  async function handleDeleteTrip(tripId: string) {
    if (deletingTripId) {
      return;
    }

    setDeletingTripId(tripId);
    setWorkspaceError(null);

    try {
      const nextAuthSnapshot = await resolveWorkspaceAuthSnapshot(
        supabase,
        setAuthSnapshot,
      );

      if (!nextAuthSnapshot) {
        throw new Error("Sign in to delete saved trips.");
      }

      await deleteTrip(tripId, nextAuthSnapshot.accessToken);
      removeCachedThreadMessages(tripId);
      prefetchedWorkspaceRef.current.delete(tripId);
      tripPrefetchPromiseRef.current.delete(tripId);
      setFreshTripIds((current) => current.filter((id) => id !== tripId));

      const nextRecentTrips = recentTrips.filter((trip) => trip.trip_id !== tripId);
      setRecentTrips(nextRecentTrips);

      if (window.localStorage.getItem(LAST_ACTIVE_TRIP_STORAGE_KEY) === tripId) {
        window.localStorage.removeItem(LAST_ACTIVE_TRIP_STORAGE_KEY);
      }

      const deletedActiveTrip =
        tripId === requestedTripId || tripId === displayedTripId;

      if (!deletedActiveTrip) {
        return;
      }

      const nextParams = new URLSearchParams(searchParams.toString());
      const nextTripId = nextRecentTrips[0]?.trip_id ?? null;

      if (nextTripId) {
        nextParams.set("trip", nextTripId);
      } else {
        nextParams.delete("trip");
      }

      nextParams.delete("new");
      setPendingTripId(null);
      setClientSelectedTripId(nextTripId);
      setWorkspace(
        buildEphemeralWorkspace(
          window.sessionStorage.getItem(BROWSER_SESSION_STORAGE_KEY),
        ),
      );

      const nextQuery = nextParams.toString();
      router.replace(
        nextTripId ? `${CHAT_ROUTE}?${nextQuery}` : NEW_CHAT_ROUTE,
        { scroll: false },
      );
    } catch (caughtError) {
      setWorkspaceError(
        caughtError instanceof Error
          ? caughtError.message
          : "Could not delete this trip.",
      );
    } finally {
      setDeletingTripId(null);
    }
  }

  async function handleRenameTrip(tripId: string, nextTitle: string) {
    if (renamingTripId || deletingTripId) {
      return;
    }

    const trimmedTitle = nextTitle.trim();
    if (!trimmedTitle) {
      throw new Error("Trip title cannot be empty.");
    }

    setRenamingTripId(tripId);
    setWorkspaceError(null);

    try {
      const nextAuthSnapshot = await resolveWorkspaceAuthSnapshot(
        supabase,
        setAuthSnapshot,
      );

      if (!nextAuthSnapshot) {
        throw new Error("Sign in to rename saved trips.");
      }

      const baseDraft =
        workspace &&
        !workspace.isEphemeral &&
        workspace.trip.trip_id === tripId
          ? workspace.tripDraft
          : await getTripDraft(tripId, nextAuthSnapshot.accessToken);
      const savedDraft = await saveTripDraft(
        tripId,
        {
          ...baseDraft,
          title: trimmedTitle,
        },
        nextAuthSnapshot.accessToken,
      );

      setRecentTrips((currentTrips) =>
        currentTrips.map((trip) =>
          trip.trip_id === tripId
            ? {
                ...trip,
                title: savedDraft.title,
                updated_at:
                  savedDraft.status.last_updated_at ??
                  trip.updated_at,
              }
            : trip,
        ),
      );

      setWorkspace((currentWorkspace) => {
        if (
          !currentWorkspace ||
          currentWorkspace.isEphemeral ||
          currentWorkspace.trip.trip_id !== tripId
        ) {
          return currentWorkspace;
        }

        return {
          ...currentWorkspace,
          trip: {
            ...currentWorkspace.trip,
            title: savedDraft.title,
          },
          tripDraft: savedDraft,
        };
      });

      const prefetchedWorkspace = prefetchedWorkspaceRef.current.get(tripId);
      if (prefetchedWorkspace) {
        prefetchedWorkspaceRef.current.set(tripId, {
          ...prefetchedWorkspace,
          trip: {
            ...prefetchedWorkspace.trip,
            title: savedDraft.title,
          },
          tripDraft: savedDraft,
        });
      }
    } catch (caughtError) {
      setWorkspaceError(
        caughtError instanceof Error
          ? caughtError.message
          : "Could not rename this trip.",
      );
    } finally {
      setRenamingTripId(null);
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
        activeTripId={requestedTripId}
        collapsed={isSidebarCollapsed}
        onSelectTrip={(tripId) => {
          void handleSelectTrip(tripId);
        }}
        onPrefetchTrip={(tripId) => {
          void handlePrefetchTrip(tripId);
        }}
        onToggleCollapsed={() => setIsSidebarCollapsed((current) => !current)}
        onCreateTrip={handleCreateTrip}
        onRenameTrip={handleRenameTrip}
        onDeleteTrip={handleDeleteTrip}
        isCreatingTrip={isCreatingTrip}
        renamingTripId={renamingTripId}
        deletingTripId={deletingTripId}
        workspace={workspace}
        recentTrips={recentTrips}
      />

      <div className="min-h-0 border-r border-[color:var(--chat-rail-border)] bg-[color:var(--chat-pane-bg)]">
        <TravelPlannerAssistant
          activeTripId={displayedTripId}
          authSnapshot={authSnapshot}
          skipInitialHistorySync={Boolean(
            (displayedTripId && freshTripIds.includes(displayedTripId)) ||
              workspace?.isEphemeral,
          )}
          isSwitchingTrips={isSwitchingTrips}
          requestedTripId={requestedTripId}
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
          authSnapshot={authSnapshot}
          workspace={workspace}
          isBootstrapping={isBootstrapping && !isSwitchingTrips}
          isSwitchingTrips={isSwitchingTrips}
          requestedTripId={requestedTripId}
          onAction={setPendingBoardAction}
        />
      </div>
    </section>
  );
}


async function resolveWorkspaceAuthSnapshot(
  supabase: ReturnType<typeof createSupabaseBrowserClient>,
  setAuthSnapshot: Dispatch<SetStateAction<BrowserAuthSnapshot | null>>,
) {
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
  options: {
    forceNewChat: boolean;
    selectedTripId: string | null;
    rememberedTripId: string | null;
    recentTrips: TripListItemResponse[];
    loadTripWorkspace: (
      tripId: string,
      signal: AbortSignal,
    ) => Promise<PlannerWorkspaceState>;
    signal: AbortSignal;
  },
): Promise<{
  workspace: PlannerWorkspaceState;
  didCreateTrip: boolean;
}> {
  if (options.forceNewChat && !options.selectedTripId) {
    return {
      workspace: buildEphemeralWorkspace(
        window.sessionStorage.getItem(BROWSER_SESSION_STORAGE_KEY),
      ),
      didCreateTrip: false,
    };
  }

  const preferredTripId =
    options.selectedTripId ?? options.rememberedTripId;

  if (preferredTripId) {
    try {
      return {
        workspace: await options.loadTripWorkspace(preferredTripId, options.signal),
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
      if (isEphemeralTripId(recentTrip.trip_id)) {
        continue;
      }

      if (recentTrip.trip_id === preferredTripId) {
        continue;
      }

      try {
        return {
          workspace: await options.loadTripWorkspace(
            recentTrip.trip_id,
            options.signal,
          ),
          didCreateTrip: false,
        };
      } catch {
        // Skip broken auto-selected trips and keep trying older saved sessions.
      }
    }
  }

  return {
    workspace: buildEphemeralWorkspace(
      window.sessionStorage.getItem(BROWSER_SESSION_STORAGE_KEY),
    ),
    didCreateTrip: false,
  };
}

async function loadWorkspaceForTrip(
  tripId: string,
  accessToken: string,
  signal?: AbortSignal,
): Promise<PlannerWorkspaceState> {
  const [trip, tripDraft] = await Promise.all([
    getTrip(tripId, accessToken, signal),
    getTripDraft(tripId, accessToken, signal),
  ]);

  return {
    browserSession: {
      browser_session_id: trip.browser_session_id,
      user_id: null,
      timezone: null,
      locale: null,
      status: "active",
      created_at: "",
    },
    isEphemeral: false,
    trip,
    tripDraft,
  };
}

async function loadTripWorkspaceWithPrefetch(
  tripId: string,
  accessToken: string,
  signal: AbortSignal,
  prefetchedWorkspace: Map<string, PlannerWorkspaceState>,
) {
  const cachedWorkspace = prefetchedWorkspace.get(tripId);
  if (cachedWorkspace) {
    prefetchedWorkspace.delete(tripId);
    return cachedWorkspace;
  }

  return await loadWorkspaceForTrip(tripId, accessToken, signal);
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
    const response = await withAbortableTimeout(
      (signal) => listTrips(RECENT_TRIPS_LIMIT, accessToken, signal),
      TRIP_LIST_BOOTSTRAP_TIMEOUT_MS,
      "Timed out while loading saved trips.",
    );

    return {
      items: sortRecentTripsByActivity(filterMeaningfulRecentTrips(response.items)),
    };
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
      setRecentTrips((currentTrips) =>
        mergeRecentTripsForSidebarRefresh(currentTrips, nextTrips.items),
      );
    }
  } catch {
    // Keep the current workspace responsive even if the sidebar list refresh fails.
  }
}

function readLastActiveTripId() {
  if (typeof window === "undefined") {
    return null;
  }

  const storedTripId = window.localStorage.getItem(LAST_ACTIVE_TRIP_STORAGE_KEY);
  if (!storedTripId || !storedTripId.trim()) {
    return null;
  }

  return storedTripId.startsWith("draft_trip_") ? null : storedTripId;
}

function readInitialWorkspace(routeSelectedTripId: string | null) {
  const initialTripId = routeSelectedTripId ?? readLastActiveTripId();
  return readWorkspaceCache(initialTripId);
}

function updateTripUrlWithoutNavigation(tripId: string) {
  const nextUrl = `${CHAT_ROUTE}?trip=${encodeURIComponent(tripId)}`;
  if (window.location.pathname === CHAT_ROUTE && window.location.search === `?trip=${tripId}`) {
    return;
  }

  window.history.pushState(null, "", nextUrl);
}

function getWorkspaceCacheKey(tripId: string) {
  return `${WORKSPACE_CACHE_PREFIX}${tripId}`;
}

function readWorkspaceCache(tripId: string | null | undefined) {
  if (typeof window === "undefined" || !tripId || isEphemeralTripId(tripId)) {
    return null;
  }

  try {
    const cachedValue = window.sessionStorage.getItem(getWorkspaceCacheKey(tripId));
    if (!cachedValue) {
      return null;
    }

    const parsedValue = JSON.parse(cachedValue) as Partial<PlannerWorkspaceState>;
    if (
      parsedValue?.isEphemeral ||
      parsedValue?.trip?.trip_id !== tripId ||
      parsedValue?.tripDraft?.trip_id !== tripId
    ) {
      window.sessionStorage.removeItem(getWorkspaceCacheKey(tripId));
      return null;
    }

    return parsedValue as PlannerWorkspaceState;
  } catch {
    window.sessionStorage.removeItem(getWorkspaceCacheKey(tripId));
    return null;
  }
}

function writeWorkspaceCache(workspace: PlannerWorkspaceState) {
  if (
    typeof window === "undefined" ||
    workspace.isEphemeral ||
    isEphemeralTripId(workspace.trip.trip_id)
  ) {
    return;
  }

  try {
    window.sessionStorage.setItem(
      getWorkspaceCacheKey(workspace.trip.trip_id),
      JSON.stringify(workspace),
    );
  } catch {
    // Session cache is a navigation nicety; the live backend state remains authoritative.
  }
}

function mergeRecentTripsWithWorkspace(
  recentTrips: TripListItemResponse[],
  workspace: PlannerWorkspaceState,
) {
  const currentTrip = buildRecentTripItem(workspace);
  const nextTrips = [
    currentTrip,
    ...recentTrips.filter((trip) => trip.trip_id !== currentTrip.trip_id),
  ];

  return sortRecentTripsByActivity(filterMeaningfulRecentTrips(nextTrips));
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
    latest_brochure_snapshot_id: null,
    latest_brochure_version: null,
    brochure_versions_count: 0,
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

function shouldRefreshRecentTrips(
  cacheKey: string,
  lastRefreshCacheKey: string | null,
  currentTrips: TripListItemResponse[],
) {
  if (lastRefreshCacheKey !== cacheKey) {
    return true;
  }

  return filterMeaningfulRecentTrips(currentTrips).length <= 1;
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
