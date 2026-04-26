"use client";

import { Plane } from "lucide-react";

import type { BudgetPosture, FlightDetail } from "@/types/trip-draft";
import { cn } from "@/lib/utils";

export type FlightCardMode = "selected" | "candidate";

export function FlightCard({
  flight,
  returnFlight,
  mode = "candidate",
  budgetContext,
}: {
  flight: FlightDetail | null | undefined;
  returnFlight?: FlightDetail | null;
  mode?: FlightCardMode;
  budgetContext?: FlightBudgetContext;
}) {
  const isBestFitEstimate = flight?.inventory_source === "placeholder";
  const title = mode === "selected" ? "Selected flight route" : "Flight options";
  const emptyMessage =
    mode === "selected"
      ? "Selected flight details will appear here once the flight step is complete."
      : "Flight options will appear here once a provider returns usable route and date detail.";

  return (
    <section className="rounded-xl bg-[color:var(--accent)] px-5 py-5 text-white">
      <div className="flex items-center justify-between gap-3">
        <p className="font-label text-[10px] uppercase tracking-[0.16em] text-white/68">
          {title}
        </p>
        {flight ? (
          <span className="rounded-full bg-white/12 px-2.5 py-1 text-[10px] font-semibold uppercase tracking-[0.12em] text-white/72">
            {isBestFitEstimate ? "Best fit" : mode === "selected" ? "Working pick" : "Candidate"}
          </span>
        ) : null}
      </div>

      {flight ? (
        <div className="mt-4 space-y-4">
          <FlightRoutePanel flight={flight} label="Outbound" budgetContext={budgetContext} />
          {returnFlight ? (
            <div className="border-t border-white/18 pt-4">
              <FlightRoutePanel
                flight={returnFlight}
                label="Return"
                compact
                budgetContext={budgetContext}
              />
            </div>
          ) : null}
        </div>
      ) : (
        <p className="mt-4 text-sm leading-7 text-white/78">{emptyMessage}</p>
      )}
    </section>
  );
}

function FlightRoutePanel({
  flight,
  label,
  compact = false,
  budgetContext,
}: {
  flight: FlightDetail;
  label: string;
  compact?: boolean;
  budgetContext?: FlightBudgetContext;
}) {
  const facts = buildFlightFacts(flight, budgetContext);
  const routeNotes = buildFlightRouteNotes(flight);

  return (
    <div>
      <p className="text-[10px] font-semibold uppercase tracking-[0.14em] text-white/60">
        {label}
      </p>
      <div className={cn("mt-3 rounded-lg bg-white/10 px-3 py-3", compact && "py-2.5")}>
        <div className="flex items-center justify-between gap-3">
          <AirportCode
            code={flight.departure_airport}
            label="Depart"
            time={formatFlightTime(flight.departure_time)}
          />
          <FlightRouteSummary flight={flight} />
          <AirportCode
            code={flight.arrival_airport}
            align="right"
            label="Arrive"
            time={formatFlightTime(flight.arrival_time)}
          />
        </div>
        <p className="mt-3 truncate text-center text-xs font-semibold text-white/76">
          {formatRouteText(flight)}
        </p>
        {formatConnectionText(flight) ? (
          <p className="mt-1 text-center text-xs leading-5 text-white/62">
            {formatConnectionText(flight)}
          </p>
        ) : null}
      </div>

      {facts.length ? (
        <div className="mt-3 flex flex-wrap items-center gap-2">
          {facts.map((fact) => (
            <span
              key={fact}
              className="rounded-md bg-white/12 px-2.5 py-1 text-xs font-semibold text-white/84"
            >
              {fact}
            </span>
          ))}
        </div>
      ) : null}

      {routeNotes.length ? (
        <div className="mt-3 space-y-1.5">
          {routeNotes.map((note) => (
            <p
              key={note}
              className="rounded-lg bg-white/10 px-3 py-2 text-xs leading-5 text-white/76"
            >
              {note}
            </p>
          ))}
        </div>
      ) : null}
    </div>
  );
}

function FlightRouteSummary({ flight }: { flight: FlightDetail }) {
  return (
    <div className="flex min-w-0 flex-1 flex-col items-center px-2 text-center">
      <Plane className="h-4 w-4 text-white/78" />
      <div className="mt-2 flex w-full items-center gap-2">
        <span className="h-1.5 w-1.5 shrink-0 rounded-full bg-white/62" />
        <span className="h-px min-w-6 flex-1 bg-white/30" />
        <span className="h-1.5 w-1.5 shrink-0 rounded-full bg-white/62" />
      </div>
      <p className="mt-2 text-[10px] font-semibold uppercase tracking-[0.14em] text-white/66">
        {formatFlightRouteDuration(flight)}
      </p>
    </div>
  );
}

function AirportCode({
  code,
  align = "left",
  label,
  time,
}: {
  code: string;
  align?: "left" | "right";
  label: string;
  time?: string | null;
}) {
  return (
    <div className={cn("min-w-[4.5rem]", align === "right" && "text-right")}>
      <p className="text-[10px] font-semibold uppercase tracking-[0.14em] text-white/52">
        {label}
      </p>
      <p className="mt-1 font-display text-3xl leading-none">{code}</p>
      {time ? (
        <p className="mt-1.5 text-[11px] font-semibold uppercase tracking-[0.12em] text-white/72">
          {time}
        </p>
      ) : null}
    </div>
  );
}

type FlightBudgetContext = {
  adults?: number | null;
  children?: number | null;
  budgetPosture?: BudgetPosture | null;
  currency?: string | null;
};

function buildFlightFacts(flight: FlightDetail, budgetContext?: FlightBudgetContext) {
  return [
    formatFare(flight, budgetContext),
    formatFlightStopLabel(flight.stop_count),
  ].filter(Boolean) as string[];
}

function formatFlightRouteDuration(flight: FlightDetail) {
  if (
    flight.inventory_source === "placeholder" ||
    flight.duration_text?.toLowerCase() === "schedule pending"
  ) {
    return "Best-fit route";
  }
  return flight.duration_text || "Time pending";
}

function buildFlightRouteNotes(flight: FlightDetail) {
  const notes = flight.notes ?? [];
  return notes
    .filter((note) => {
      const normalized = note.toLowerCase();
      return (
        !normalized.startsWith("estimated fare:") &&
        !normalized.includes("planning placeholder") &&
        !normalized.includes("schedule") &&
        !normalized.includes("before booking") &&
        !normalized.startsWith("direct ") &&
        !normalized.includes("direct route") &&
        !normalized.includes("direct outbound route") &&
        !normalized.includes("direct return route") &&
        !normalized.includes("stop(s)") &&
        !normalized.includes("connection detail")
      );
    })
    .slice(0, 2);
}

function formatRouteText(flight: FlightDetail) {
  return `${flight.departure_airport} to ${flight.arrival_airport}`;
}

function formatConnectionText(flight: FlightDetail) {
  const detailedAirports = buildDetailedAirportPath(flight);
  const connectionAirports = detailedAirports.slice(1, -1);
  if (connectionAirports.length > 0) {
    return `via ${connectionAirports.join(", ")}`;
  }

  const stopLabel = formatFlightStopLabel(flight.stop_count);
  if (!stopLabel || flight.stop_count === 0) {
    return stopLabel;
  }

  return `${stopLabel}; connection airports not supplied yet`;
}

function buildDetailedAirportPath(flight: FlightDetail) {
  const legs = flight.legs ?? [];
  if (legs.length < 2) {
    return [];
  }

  const airports = [legs[0]?.departure_airport, ...legs.map((leg) => leg.arrival_airport)]
    .filter(Boolean)
    .map((airport) => airport.trim());
  return Array.from(new Set(airports));
}

function formatFare(flight: FlightDetail, budgetContext?: FlightBudgetContext) {
  if (typeof flight.fare_amount === "number" && flight.fare_currency) {
    return new Intl.NumberFormat("en-GB", {
      style: "currency",
      currency: flight.fare_currency.toUpperCase(),
      maximumFractionDigits: 0,
    }).format(flight.fare_amount);
  }

  return cleanPriceText(flight.price_text) ?? estimateFallbackFlightBudget(flight, budgetContext);
}

function cleanPriceText(value: string | null | undefined) {
  if (!value) {
    return null;
  }

  const prefixes = ["Cached fare snapshot:", "Live fare snapshot:"];
  for (const prefix of prefixes) {
    if (value.startsWith(prefix)) {
      return value.slice(prefix.length).trim();
    }
  }
  return value;
}

function estimateFallbackFlightBudget(
  flight: FlightDetail,
  budgetContext?: FlightBudgetContext,
) {
  if (flight.inventory_source !== "placeholder" || flight.direction !== "outbound") {
    return null;
  }
  const adults = Math.max(budgetContext?.adults ?? 1, 1);
  const children = Math.max(budgetContext?.children ?? 0, 0);
  const travelers = adults + children;
  const [lowPerPerson, highPerPerson] = estimateFallbackPerPersonBand(
    flight.departure_airport,
    flight.arrival_airport,
    budgetContext?.budgetPosture ?? "mid_range",
  );
  const currency = budgetContext?.currency ?? "GBP";
  const low = lowPerPerson * travelers;
  const high = highPerPerson * travelers;
  return `Flight budget ${currency} ${formatCompactAmount(low)}-${formatCompactAmount(high)} total`;
}

function estimateFallbackPerPersonBand(
  origin: string,
  destination: string,
  posture: BudgetPosture,
) {
  const originRegion = estimateRegion(origin);
  const destinationRegion = estimateRegion(destination);
  let base: [number, number] = [220, 520];
  if (originRegion === "europe" && destinationRegion === "europe") {
    base = [120, 280];
  } else if (originRegion !== destinationRegion && [originRegion, destinationRegion].includes("asia")) {
    base = [650, 1050];
  } else if (originRegion !== destinationRegion) {
    base = [480, 900];
  }

  if (posture === "premium") {
    return [Math.round(base[0] * 1.35), Math.round(base[1] * 1.55)] as const;
  }
  if (posture === "budget") {
    return [Math.round(base[0] * 0.78), Math.round(base[1] * 0.9)] as const;
  }
  return base;
}

function estimateRegion(code: string) {
  const normalized = code.toUpperCase();
  if (["LON", "LGW", "LHR", "STN", "LTN", "LCY", "MAN", "BHX", "EDI", "GLA", "PAR", "ROM", "MIL", "MAD", "BCN", "LIS", "OPO", "AMS", "BER", "PRG", "BUD", "ZRH", "NAP", "PSA"].includes(normalized)) {
    return "europe";
  }
  if (["OSA", "KIX", "ITM", "TYO", "HND", "NRT", "DXB"].includes(normalized)) {
    return "asia";
  }
  if (["NYC", "JFK", "EWR", "LGA", "SFO", "LAX", "YYC", "CUN"].includes(normalized)) {
    return "north_america";
  }
  return "other";
}

function formatCompactAmount(value: number) {
  return new Intl.NumberFormat("en-GB", {
    maximumFractionDigits: 0,
  }).format(value);
}

function formatFlightTime(value: string | Date | null | undefined) {
  if (!value) {
    return null;
  }

  const parsed = value instanceof Date ? value : new Date(value);
  if (Number.isNaN(parsed.getTime())) {
    return null;
  }

  return new Intl.DateTimeFormat("en-GB", {
    hour: "2-digit",
    minute: "2-digit",
  }).format(parsed);
}

function formatFlightStopLabel(value: number | null | undefined) {
  if (value == null) {
    return null;
  }
  if (value === 0) {
    return "Direct";
  }
  if (value === 1) {
    return "1 stop";
  }
  return `${value} stops`;
}
