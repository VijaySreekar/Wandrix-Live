"use client";

import {
  CloudSun,
  Plane,
} from "lucide-react";

import type {
  ActivityDetail,
  FlightDetail,
  HotelStayDetail,
  WeatherDetail,
} from "@/types/trip-draft";
import { cn } from "@/lib/utils";

export function FlightCard({ flight }: { flight: FlightDetail | undefined }) {
  return (
    <section className="rounded-xl bg-[color:var(--accent)] px-5 py-5 text-white">
      <p className="font-label text-[10px] uppercase tracking-[0.16em] text-white/68">
        Outbound flight
      </p>
      {flight ? (
        <>
          <div className="mt-5 flex items-end justify-between gap-4">
            <AirportCode code={flight.departure_airport} />
            <div className="flex flex-1 flex-col items-center px-3">
              <Plane className="h-4 w-4 text-white/74" />
              <div className="mt-2 h-px w-full border-t border-dashed border-white/34" />
              <p className="mt-2 text-[10px] uppercase tracking-[0.16em] text-white/66">
                {flight.duration_text || "Flight time"}
              </p>
            </div>
            <AirportCode code={flight.arrival_airport} align="right" />
          </div>
          <div className="mt-5 rounded-lg bg-white/12 px-4 py-3 text-sm">
            <div className="flex items-center justify-between gap-3">
              <span>{flight.carrier}</span>
              <span className="font-semibold">
                {flight.flight_number || "TBD"}
              </span>
            </div>
          </div>
        </>
      ) : (
        <p className="mt-4 text-sm leading-7 text-white/78">
          Flight details will appear here once the planner has enough route and
          date context.
        </p>
      )}
    </section>
  );
}

export function WeatherCard({ forecasts }: { forecasts: WeatherDetail[] }) {
  const displayForecasts =
    forecasts.length > 0
      ? forecasts
      : [
          {
            id: "weather-placeholder-1",
            day_label: "Wed",
            summary: "",
            high_c: null,
            low_c: null,
            notes: [],
          },
          {
            id: "weather-placeholder-2",
            day_label: "Thu",
            summary: "",
            high_c: null,
            low_c: null,
            notes: [],
          },
          {
            id: "weather-placeholder-3",
            day_label: "Fri",
            summary: "",
            high_c: null,
            low_c: null,
            notes: [],
          },
        ];

  return (
    <section className="rounded-xl border border-shell-border/70 bg-[linear-gradient(135deg,color-mix(in_srgb,var(--accent)_10%,white),color-mix(in_srgb,var(--accent2)_10%,white))] px-5 py-5">
      <p className="font-label text-[10px] uppercase tracking-[0.16em] text-foreground/50">
        Forecast
      </p>
      <div className="mt-4 flex items-center gap-4">
        <CloudSun className="h-12 w-12 text-[color:var(--accent)]" />
        <div>
          <p className="font-display text-4xl leading-none text-[color:var(--accent)]">
            {forecasts[0] ? formatPrimaryTemperature(forecasts[0]) : "—"}
          </p>
          <p className="mt-1 text-sm text-foreground/60">
            {forecasts[0]?.summary || "Weather will appear when dates are locked."}
          </p>
        </div>
      </div>
      <div className="mt-5 grid grid-cols-3 gap-3 rounded-lg bg-white/55 px-4 py-3">
        {displayForecasts.map((forecast) => (
          <div key={forecast.id} className="text-center">
            <p className="text-[10px] uppercase tracking-[0.16em] text-foreground/50">
              {forecast.day_label}
            </p>
            <CloudSun className="mx-auto mt-2 h-4 w-4 text-[color:var(--accent)]" />
            <p className="mt-2 text-xs font-semibold text-foreground">
              {formatTemperatureBand(forecast.high_c, forecast.low_c)}
            </p>
          </div>
        ))}
      </div>
    </section>
  );
}

export function HotelSummary({ hotel }: { hotel: HotelStayDetail }) {
  return (
    <div className="overflow-hidden rounded-xl bg-background">
      <div className="h-28 bg-[linear-gradient(135deg,color-mix(in_srgb,var(--accent)_18%,transparent),color-mix(in_srgb,var(--accent2)_16%,transparent))]" />
      <div className="px-4 py-4">
        <p className="text-lg font-semibold text-foreground">{hotel.hotel_name}</p>
        <p className="mt-1 text-sm text-foreground/58">
          {hotel.area || "Area still being refined"}
        </p>
        <p className="mt-3 text-sm leading-7 text-foreground/66">
          {formatDateRange(hotel.check_in, hotel.check_out)}
        </p>
        {hotel.notes[0] ? (
          <p className="mt-2 text-sm leading-7 text-foreground/66">
            {hotel.notes[0]}
          </p>
        ) : null}
      </div>
    </div>
  );
}

export function ActivityFeature({
  activity,
  destination,
}: {
  activity: ActivityDetail;
  destination: string | null;
}) {
  return (
    <div className="overflow-hidden rounded-xl bg-background">
      <div
        className="h-32"
        style={buildActivityVisualStyle(destination, activity)}
        aria-hidden="true"
      />
      <div className="px-4 py-4">
        <p className="text-lg font-semibold text-foreground">{activity.title}</p>
        <p className="mt-1 text-sm text-foreground/56">
          {[activity.category, activity.day_label].filter(Boolean).join(" • ") ||
            "Trip highlight"}
        </p>
        {activity.notes[0] ? (
          <p className="mt-3 text-sm leading-7 text-foreground/66">
            {activity.notes[0]}
          </p>
        ) : null}
      </div>
    </div>
  );
}

export function getLiveDestinationImage(destination: string | null) {
  const normalized = destination?.toLowerCase() ?? "";

  if (normalized.includes("kyoto")) {
    return "https://images.unsplash.com/photo-1493976040374-85c8e12f0c0e?auto=format&fit=crop&w=1400&q=80";
  }

  if (normalized.includes("barcelona")) {
    return "https://images.unsplash.com/photo-1539037116277-4db20889f2d4?auto=format&fit=crop&w=1400&q=80";
  }

  if (normalized.includes("lisbon")) {
    return "https://images.unsplash.com/photo-1513735492246-483525079686?auto=format&fit=crop&w=1400&q=80";
  }

  if (normalized.includes("amalfi")) {
    return "https://images.unsplash.com/photo-1612698093158-e07ac200d44e?auto=format&fit=crop&w=1400&q=80";
  }

  if (destination) {
    return `https://source.unsplash.com/1400x900/?${encodeURIComponent(`${destination} travel landscape`)}`;
  }

  return "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=1400&q=80";
}

function AirportCode({
  code,
  align = "left",
}: {
  code: string;
  align?: "left" | "right";
}) {
  return (
    <div className={cn("min-w-[4rem]", align === "right" && "text-right")}>
      <p className="font-display text-4xl leading-none">{code}</p>
    </div>
  );
}

function buildActivityVisualStyle(
  destination: string | null,
  activity: ActivityDetail,
) {
  const query = encodeURIComponent(
    [destination, activity.category, activity.title].filter(Boolean).join(" "),
  );

  return {
    backgroundImage: `linear-gradient(135deg, color-mix(in srgb, var(--accent) 14%, transparent), color-mix(in srgb, var(--accent2) 12%, transparent)), url(https://source.unsplash.com/900x700/?${query})`,
    backgroundSize: "cover",
    backgroundPosition: "center",
  } as const;
}

function formatDateRange(startDate: string | null, endDate: string | null) {
  return `${formatDateShort(startDate)} through ${formatDateShort(endDate)}`;
}

function formatDateShort(value: string | null) {
  if (!value) {
    return "TBD";
  }

  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) {
    return value;
  }

  return new Intl.DateTimeFormat("en-GB", {
    day: "numeric",
    month: "short",
  }).format(parsed);
}

function formatTemperatureBand(high: number | null, low: number | null) {
  if (high == null && low == null) {
    return "TBD";
  }

  if (high != null && low != null) {
    return `${Math.round(low)}° to ${Math.round(high)}°`;
  }

  return `${Math.round(high ?? low ?? 0)}°`;
}

function formatPrimaryTemperature(forecast: WeatherDetail) {
  if (forecast.high_c == null && forecast.low_c == null) {
    return "—";
  }

  return `${Math.round(forecast.high_c ?? forecast.low_c ?? 0)}°`;
}
