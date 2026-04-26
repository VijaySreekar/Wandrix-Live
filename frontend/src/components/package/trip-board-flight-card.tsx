"use client";

import { Plane } from "lucide-react";

import type { FlightDetail } from "@/types/trip-draft";
import { cn } from "@/lib/utils";

export type FlightCardMode = "selected" | "candidate";

export function FlightCard({
  flight,
  returnFlight,
  mode = "candidate",
}: {
  flight: FlightDetail | null | undefined;
  returnFlight?: FlightDetail | null;
  mode?: FlightCardMode;
}) {
  const title = mode === "selected" ? "Selected flights" : "Flight options";
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
            {mode === "selected" ? "Working pick" : "Candidate"}
          </span>
        ) : null}
      </div>

      {flight ? (
        <div className="mt-4 space-y-4">
          <FlightRoutePanel flight={flight} label="Outbound" />
          {returnFlight ? (
            <div className="border-t border-white/18 pt-4">
              <FlightRoutePanel flight={returnFlight} label="Return" compact />
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
}: {
  flight: FlightDetail;
  label: string;
  compact?: boolean;
}) {
  const facts = buildFlightFacts(flight);
  const needsScheduleCheck = flight.inventory_source === "cached" || !flight.arrival_time;

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

      {needsScheduleCheck ? (
        <p className="mt-2 text-xs leading-5 text-white/64">
          Live schedule check still needed before booking.
        </p>
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
        {flight.duration_text || "Time pending"}
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

function buildFlightFacts(flight: FlightDetail) {
  return [
    formatFare(flight),
    formatFlightStopLabel(flight.stop_count),
  ].filter(Boolean) as string[];
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

function formatFare(flight: FlightDetail) {
  if (typeof flight.fare_amount === "number" && flight.fare_currency) {
    return new Intl.NumberFormat("en-GB", {
      style: "currency",
      currency: flight.fare_currency.toUpperCase(),
      maximumFractionDigits: 0,
    }).format(flight.fare_amount);
  }

  return cleanPriceText(flight.price_text);
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
