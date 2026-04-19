import Link from "next/link";

import type { TimelineItem } from "@/types/trip-draft";
import type { PlannerWorkspaceState } from "@/types/planner-workspace";

type TripBoardPreviewProps = {
  workspace: PlannerWorkspaceState | null;
  isBootstrapping: boolean;
  lastDraftChanges: string[];
};

export function TripBoardPreview({
  workspace,
  isBootstrapping,
  lastDraftChanges,
}: TripBoardPreviewProps) {
  if (isBootstrapping) {
    return (
      <section className="bg-shell">
        <div className="border-b border-shell-border px-5 py-4">
          <h2 className="text-base font-semibold text-foreground">Trip board</h2>
          <p className="mt-1 text-sm text-foreground/68">Preparing draft state</p>
        </div>
        <div className="px-5 py-5">
          <p className="text-sm leading-7 text-foreground/75">
            The saved trip board is loading. Once the conversation starts, this
            area will reflect the structured trip draft in real time.
          </p>
        </div>
      </section>
    );
  }

  if (!workspace) {
    return (
      <section className="bg-shell">
        <div className="border-b border-shell-border px-5 py-4">
          <h2 className="text-base font-semibold text-foreground">Trip board</h2>
          <p className="mt-1 text-sm text-foreground/68">Trip board unavailable</p>
        </div>
        <div className="px-5 py-5">
          <p className="text-sm leading-7 text-foreground/75">
            Sign in and start a trip workspace to see the structured planning
            board on this side.
          </p>
        </div>
      </section>
    );
  }

  const { configuration, status, module_outputs: moduleOutputs } = workspace.tripDraft;
  const selectedModules = Object.entries(configuration.selected_modules)
    .filter(([, enabled]) => enabled)
    .map(([moduleName]) => moduleName);
  const visibleTimeline = workspace.tripDraft.timeline.slice(0, 6);
  const weatherHighlights = moduleOutputs.weather.slice(0, 4);
  const activityHighlights = moduleOutputs.activities.slice(0, 4);
  const moduleCards = [
    {
      label: "Flights",
      enabled: configuration.selected_modules.flights,
      count: workspace.tripDraft.timeline.filter((item) => item.type === "flight").length,
      href: `/flights?trip=${workspace.trip.trip_id}`,
    },
    {
      label: "Hotels",
      enabled: configuration.selected_modules.hotels,
      count: workspace.tripDraft.timeline.filter((item) => item.type === "hotel").length,
      href: `/hotels?trip=${workspace.trip.trip_id}`,
    },
    {
      label: "Activities",
      enabled: configuration.selected_modules.activities,
      count: workspace.tripDraft.timeline.filter((item) => item.type === "activity").length,
      href: `/activities?trip=${workspace.trip.trip_id}`,
    },
    {
      label: "Weather",
      enabled: configuration.selected_modules.weather,
      count: workspace.tripDraft.timeline.filter((item) => item.type === "weather").length,
      href: null,
    },
  ];

  return (
    <section className="bg-shell">
      <div className="border-b border-shell-border px-5 py-4">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <h2 className="text-xl font-semibold tracking-tight text-foreground">
              {workspace.tripDraft.title}
            </h2>
            <p className="mt-1 text-sm text-foreground/68">
              {formatRoute(
                configuration.from_location,
                configuration.to_location,
              )}{" "}
              |{" "}
              {formatDateWindow(configuration.start_date, configuration.end_date)}
            </p>
          </div>

          <Link
            href={`/brochure/${workspace.trip.trip_id}`}
            className="rounded-md border border-shell-border px-3 py-2 text-sm font-medium text-foreground transition-colors hover:bg-panel"
          >
            Open brochure
          </Link>
        </div>
      </div>

      <div className="grid gap-4 p-5">
        <div className="grid gap-3 rounded-lg border border-shell-border bg-panel px-4 py-4 sm:grid-cols-2 xl:grid-cols-3">
          <BoardStat
            label="Planning phase"
            value={formatPhase(status.phase)}
          />
          <BoardStat
            label="Travelers"
            value={`${configuration.travelers.adults} adults, ${configuration.travelers.children} children`}
          />
          <BoardStat
            label="Budget"
            value={
              configuration.budget_gbp
                ? `GBP ${configuration.budget_gbp.toLocaleString()}`
                : "Budget still open"
            }
          />
          <BoardStat
            label="Selected modules"
            value={selectedModules.length > 0 ? selectedModules.join(", ") : "Still being chosen"}
          />
          <BoardStat
            label="Activity tone"
            value={
              configuration.activity_styles.length > 0
                ? configuration.activity_styles.join(", ")
                : "Still being shaped"
            }
          />
          <BoardStat
            label="Timeline blocks"
            value={String(workspace.tripDraft.timeline.length)}
          />
        </div>

        <div className="grid gap-4 xl:grid-cols-[minmax(0,1.15fr)_minmax(0,0.85fr)]">
          <section className="rounded-lg border border-shell-border bg-panel px-4 py-4">
            <div className="flex items-center justify-between gap-3">
              <h3 className="text-sm font-semibold text-foreground">Latest planner changes</h3>
              <Link
                href={`/chat?trip=${workspace.trip.trip_id}`}
                className="text-sm font-medium text-foreground/68 transition-colors hover:text-foreground"
              >
                Open chat
              </Link>
            </div>
            {lastDraftChanges.length > 0 ? (
              <ul className="mt-3 grid gap-2 text-sm leading-7 text-foreground/75">
                {lastDraftChanges.map((change) => (
                  <li
                    key={change}
                    className="rounded-md border border-shell-border bg-background px-3 py-2"
                  >
                    {change}
                  </li>
                ))}
              </ul>
            ) : (
              <p className="mt-3 text-sm leading-7 text-foreground/75">
                Send a conversation turn and the board will summarize what changed.
              </p>
            )}
          </section>

          <section className="rounded-lg border border-shell-border bg-panel px-4 py-4">
            <h3 className="text-sm font-semibold text-foreground">Planning status</h3>
            {status.missing_fields.length > 0 ? (
              <ul className="mt-3 grid gap-2 text-sm leading-7 text-foreground/75">
                {status.missing_fields.map((fieldName) => (
                  <li
                    key={fieldName}
                    className="rounded-md border border-shell-border bg-background px-3 py-2"
                  >
                    Still needed: {fieldName}
                  </li>
                ))}
              </ul>
            ) : (
              <p className="mt-3 rounded-md border border-shell-border bg-background px-3 py-2 text-sm leading-7 text-foreground/75">
                The draft has the core trip fields needed to move into fuller planning.
              </p>
            )}
          </section>
        </div>

        <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
          {moduleCards.map((moduleCard) => (
            <article
              key={moduleCard.label}
              className="rounded-lg border border-shell-border bg-panel px-4 py-4"
            >
              <div className="flex items-center justify-between gap-3">
                <h3 className="text-sm font-semibold text-foreground">{moduleCard.label}</h3>
                <span className="rounded-md border border-shell-border bg-background px-2 py-1 text-xs text-foreground/60">
                  {moduleCard.enabled ? "Enabled" : "Off"}
                </span>
              </div>
              <p className="mt-3 text-2xl font-semibold tracking-tight text-foreground">
                {moduleCard.count}
              </p>
              <p className="mt-1 text-sm leading-7 text-foreground/72">
                {moduleCard.enabled
                  ? `${moduleCard.count} saved planning blocks are mapped here.`
                  : `${moduleCard.label} is not selected for this trip yet.`}
              </p>
              {moduleCard.href ? (
                <Link
                  href={moduleCard.href}
                  className="mt-3 inline-flex text-sm font-medium text-foreground/68 transition-colors hover:text-foreground"
                >
                  Open {moduleCard.label.toLowerCase()}
                </Link>
              ) : null}
            </article>
          ))}
        </div>

        <div className="grid gap-4 xl:grid-cols-[minmax(0,0.9fr)_minmax(0,1.1fr)]">
          <section className="rounded-lg border border-shell-border bg-panel px-4 py-4">
            <div className="flex items-center justify-between gap-3">
              <h3 className="text-sm font-semibold text-foreground">Weather outlook</h3>
              <span className="text-sm text-foreground/58">
                {weatherHighlights.length} saved forecast days
              </span>
            </div>
            {weatherHighlights.length > 0 ? (
              <div className="mt-3 grid gap-3">
                {weatherHighlights.map((forecast) => (
                  <article
                    key={forecast.id}
                    className="rounded-md border border-shell-border bg-background px-3 py-3"
                  >
                    <div className="flex items-start justify-between gap-3">
                      <div>
                        <p className="text-sm font-semibold text-foreground">
                          {forecast.day_label}
                        </p>
                        <p className="mt-1 text-sm text-foreground/70">
                          {forecast.summary}
                        </p>
                      </div>
                      <p className="text-sm font-medium text-foreground/72">
                        {formatTemperatureBand(forecast.high_c, forecast.low_c)}
                      </p>
                    </div>
                    {forecast.notes.length > 0 ? (
                      <ul className="mt-3 grid gap-2 text-sm text-foreground/65">
                        {forecast.notes.slice(0, 2).map((note) => (
                          <li key={note}>{note}</li>
                        ))}
                      </ul>
                    ) : null}
                  </article>
                ))}
              </div>
            ) : (
              <EmptySection message="Weather details will appear here once the destination and trip window are clear enough to forecast." />
            )}
          </section>

          <section className="rounded-lg border border-shell-border bg-panel px-4 py-4">
            <div className="flex items-center justify-between gap-3">
              <h3 className="text-sm font-semibold text-foreground">Destination highlights</h3>
              <Link
                href={`/activities?trip=${workspace.trip.trip_id}`}
                className="text-sm font-medium text-foreground/68 transition-colors hover:text-foreground"
              >
                Open activities
              </Link>
            </div>
            {activityHighlights.length > 0 ? (
              <div className="mt-3 grid gap-3 sm:grid-cols-2">
                {activityHighlights.map((activity) => (
                  <article
                    key={activity.id}
                    className="rounded-md border border-shell-border bg-background px-3 py-3"
                  >
                    <p className="text-sm font-semibold text-foreground">{activity.title}</p>
                    <p className="mt-1 text-sm text-foreground/62">
                      {[activity.category, activity.day_label].filter(Boolean).join(" | ") ||
                        "Trip highlight"}
                    </p>
                    {activity.time_label ? (
                      <p className="mt-2 text-sm text-foreground/72">{activity.time_label}</p>
                    ) : null}
                    {activity.notes.length > 0 ? (
                      <p className="mt-2 text-sm leading-7 text-foreground/72">
                        {activity.notes[0]}
                      </p>
                    ) : null}
                  </article>
                ))}
              </div>
            ) : (
              <EmptySection message="Destination highlights will appear here once the planner has enough route and style context." />
            )}
          </section>
        </div>

        <section className="rounded-lg border border-shell-border bg-panel px-4 py-4">
          <h3 className="text-sm font-semibold text-foreground">Timeline preview</h3>
          {visibleTimeline.length > 0 ? (
            <div className="mt-3 grid gap-3">
              {visibleTimeline.map((item) => (
                <TimelinePreviewCard key={item.id} item={item} />
              ))}
            </div>
          ) : (
            <EmptySection message="The conversation has not generated a timeline preview yet." />
          )}
        </section>
      </div>
    </section>
  );
}

function TimelinePreviewCard({ item }: { item: TimelineItem }) {
  return (
    <article className="rounded-md border border-shell-border bg-background px-3 py-3">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <p className="font-medium text-foreground">{item.title}</p>
        <span className="text-xs text-foreground/55">{item.type}</span>
      </div>
      <p className="mt-1 text-sm text-foreground/70">
        {[item.day_label, item.location_label].filter(Boolean).join(" | ") || "Draft item"}
      </p>
      {item.summary ? (
        <p className="mt-2 text-sm leading-7 text-foreground/75">{item.summary}</p>
      ) : null}
    </article>
  );
}

function EmptySection({ message }: { message: string }) {
  return (
    <p className="mt-3 rounded-md border border-shell-border bg-background px-3 py-3 text-sm leading-7 text-foreground/72">
      {message}
    </p>
  );
}

function BoardStat({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <p className="text-xs font-medium text-foreground/55">{label}</p>
      <p className="mt-1 text-sm leading-7 text-foreground/80">{value}</p>
    </div>
  );
}

function formatRoute(fromLocation: string | null, toLocation: string | null) {
  if (fromLocation || toLocation) {
    return `${fromLocation ?? "Origin"} to ${toLocation ?? "Destination"}`;
  }

  return "Route still being shaped";
}

function formatDateWindow(startDate: string | null, endDate: string | null) {
  if (startDate || endDate) {
    return `${startDate ?? "TBD"} through ${endDate ?? "TBD"}`;
  }

  return "Travel dates still open";
}

function formatPhase(value: string) {
  return value.replaceAll("_", " ");
}

function formatTemperatureBand(high: number | null, low: number | null) {
  if (high == null && low == null) {
    return "Temperatures pending";
  }

  if (high != null && low != null) {
    return `${Math.round(low)}C to ${Math.round(high)}C`;
  }

  return `${Math.round(high ?? low ?? 0)}C`;
}
