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

export function FlightCard({
  flight,
  returnFlight,
}: {
  flight: FlightDetail | null | undefined;
  returnFlight?: FlightDetail | null;
}) {
  return (
    <section className="rounded-xl bg-[color:var(--accent)] px-5 py-5 text-white">
      <p className="font-label text-[10px] uppercase tracking-[0.16em] text-white/68">
        Working flights
      </p>
      {flight ? (
        <>
          <FlightRouteRow flight={flight} label="Outbound" />
          {returnFlight ? (
            <div className="mt-4 border-t border-white/18 pt-4">
              <FlightRouteRow flight={returnFlight} label="Return" compact />
            </div>
          ) : null}
          <FlightFactPanel flight={flight} returnFlight={returnFlight} />
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

function FlightRouteRow({
  flight,
  label,
  compact = false,
}: {
  flight: FlightDetail;
  label: string;
  compact?: boolean;
}) {
  return (
    <div>
      <p className="text-[10px] font-semibold uppercase tracking-[0.14em] text-white/60">
        {label}
      </p>
      <div className={cn("mt-3 flex items-end justify-between gap-4", compact && "mt-2")}>
        <AirportCode
          code={flight.departure_airport}
          time={formatFlightTime(flight.departure_time)}
        />
        <div className="flex flex-1 flex-col items-center px-3">
          <Plane className="h-4 w-4 text-white/74" />
          <div className="mt-2 h-px w-full border-t border-dashed border-white/34" />
          <p className="mt-2 text-[10px] uppercase tracking-[0.16em] text-white/66">
            {flight.duration_text || "Flight time"}
          </p>
        </div>
        <AirportCode
          code={flight.arrival_airport}
          align="right"
          time={formatFlightTime(flight.arrival_time)}
        />
      </div>
    </div>
  );
}

function FlightFactPanel({
  flight,
  returnFlight,
}: {
  flight: FlightDetail;
  returnFlight?: FlightDetail | null;
}) {
  const facts = [
    flight.carrier,
    flight.flight_number,
    formatFlightStopLabel(flight.stop_count),
    flight.price_text,
    flight.timing_quality,
  ].filter(Boolean);
  const returnFacts = returnFlight
    ? [
        formatFlightStopLabel(returnFlight.stop_count),
        returnFlight.price_text,
        returnFlight.timing_quality,
      ].filter(Boolean)
    : [];

  return (
    <div className="mt-5 rounded-lg bg-white/12 px-4 py-3 text-sm">
      <div className="flex flex-wrap items-center gap-2">
        {facts.map((fact) => (
          <span
            key={fact}
            className="rounded-md bg-white/12 px-2.5 py-1 text-xs font-semibold text-white/84"
          >
            {fact}
          </span>
        ))}
      </div>
      {flight.layover_summary ? (
        <p className="mt-2 text-xs leading-5 text-white/72">{flight.layover_summary}</p>
      ) : null}
      {returnFacts.length ? (
        <p className="mt-2 text-xs leading-5 text-white/72">
          Return: {returnFacts.join(" · ")}
        </p>
      ) : null}
      {flight.inventory_notice ? (
        <p className="mt-2 text-xs leading-5 text-white/64">
          {flight.inventory_notice}
        </p>
      ) : null}
    </div>
  );
}

export function WeatherCard({
  forecasts,
  status,
  summary,
  influenceNotes,
}: {
  forecasts: WeatherDetail[];
  status?: "ready" | "unavailable" | "not_requested" | null;
  summary?: string | null;
  influenceNotes?: string[];
}) {
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
      <div className="flex items-center justify-between gap-3">
        <p className="font-label text-[10px] uppercase tracking-[0.16em] text-foreground/50">
          Forecast
        </p>
        <span className="rounded-full bg-background/70 px-2.5 py-1 text-[10px] font-semibold uppercase tracking-[0.12em] text-foreground/50">
          {formatWeatherStatus(status, forecasts.length)}
        </span>
      </div>
      <div className="mt-4 flex items-center gap-4">
        <CloudSun className="h-12 w-12 text-[color:var(--accent)]" />
        <div>
          <p className="font-display text-4xl leading-none text-[color:var(--accent)]">
            {forecasts[0] ? formatPrimaryTemperature(forecasts[0]) : "—"}
          </p>
          <p className="mt-1 text-sm text-foreground/60">
            {forecasts[0]?.summary ||
              summary ||
              "Weather will appear when dates are locked."}
          </p>
        </div>
      </div>
      {summary && forecasts.length > 0 ? (
        <p className="mt-4 text-xs leading-5 text-foreground/58">{summary}</p>
      ) : null}
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
            {forecast.temperature_band ? (
              <p className="mt-1 text-[10px] capitalize text-foreground/45">
                {forecast.temperature_band}
              </p>
            ) : null}
          </div>
        ))}
      </div>
      {influenceNotes?.length ? (
        <div className="mt-4 space-y-2">
          {influenceNotes.slice(0, 2).map((note) => (
            <p key={note} className="text-xs leading-5 text-foreground/58">
              {note}
            </p>
          ))}
        </div>
      ) : null}
    </section>
  );
}

export function HotelSummary({
  hotel,
  destination,
}: {
  hotel: HotelStayDetail;
  destination: string | null;
}) {
  const details = splitHotelNotes(hotel.notes);
  const heroImage = hotel.image_url;
  const pricingLabel =
    typeof hotel.nightly_rate_amount === "number"
      ? formatCurrency(hotel.nightly_rate_amount, hotel.nightly_rate_currency)
      : "Rate will firm up with exact dates";

  return (
    <div className="overflow-hidden rounded-xl bg-background">
      {heroImage ? (
        <div
          className="relative h-28 border-b border-shell-border/70 bg-cover bg-center"
          style={{
            backgroundImage: `linear-gradient(180deg, rgba(15,23,42,0.08), rgba(15,23,42,0.42)), url(${heroImage})`,
          }}
        />
      ) : (
        <div className="flex h-28 items-end border-b border-shell-border/70 bg-[linear-gradient(145deg,#fbf7ee_0%,#f3ece1_100%)] px-4 py-3">
          <div>
            <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-[#8a7657]">
              Hotel image pending
            </p>
            <p className="mt-2 text-sm font-medium text-[#2c241a]">
              {destination || hotel.area || "Stay details"}
            </p>
          </div>
        </div>
      )}
      <div className="border-b border-shell-border/70 bg-[linear-gradient(135deg,color-mix(in_srgb,var(--accent)_18%,transparent),color-mix(in_srgb,var(--accent2)_16%,transparent))] px-4 py-4">
        <div className="flex items-start justify-between gap-3">
          <div className="min-w-0">
            <p className="text-lg font-semibold text-foreground">{hotel.hotel_name}</p>
            <p className="mt-1 text-sm text-foreground/58">
              {hotel.area || "Area still being refined"}
            </p>
          </div>
          <span className="rounded-md border border-shell-border bg-background px-2.5 py-1 text-[11px] font-medium text-foreground/62">
            Stay
          </span>
        </div>
      </div>
      <div className="px-4 py-4">
        <div className="grid gap-3">
          <div className="flex items-start justify-between gap-3 rounded-lg border border-shell-border/70 bg-panel px-3 py-3">
            <div>
              <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-foreground/44">
                Stay window
              </p>
              <p className="mt-2 text-sm leading-7 text-foreground/66">
                {formatDateRange(hotel.check_in, hotel.check_out)}
              </p>
            </div>
            <div className="text-right">
              <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-foreground/44">
                Spend
              </p>
              <p className="mt-2 text-sm font-semibold text-foreground">
                {pricingLabel}
              </p>
            </div>
          </div>

          {details.highlights[0] ? (
            <p className="text-sm leading-7 text-foreground/66">
              {details.highlights[0]}
            </p>
          ) : null}
        </div>
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

  if (normalized.includes("marrakesh") || normalized.includes("marrakech")) {
    return "https://images.unsplash.com/photo-1597212720410-255d1466f5eb?auto=format&fit=crop&w=1600&q=80";
  }

  if (normalized.includes("malaga")) {
    return "https://images.unsplash.com/photo-1558642084-fd07fae5282e?auto=format&fit=crop&w=1600&q=80";
  }

  if (normalized.includes("dubai")) {
    return "https://images.unsplash.com/photo-1512453979798-5ea266f8880c?auto=format&fit=crop&w=1600&q=80";
  }

  if (
    normalized.includes("canary") ||
    normalized.includes("tenerife") ||
    normalized.includes("gran canaria")
  ) {
    return "https://images.unsplash.com/photo-1500375592092-40eb2168fd21?auto=format&fit=crop&w=1600&q=80";
  }

  if (normalized.includes("porto")) {
    return "https://images.unsplash.com/photo-1555881400-74d7acaacd8b?auto=format&fit=crop&w=1600&q=80";
  }

  if (normalized.includes("valencia")) {
    return "https://images.unsplash.com/photo-1543783207-ec64e4d95325?auto=format&fit=crop&w=1600&q=80";
  }

  if (normalized.includes("seville")) {
    return "https://images.unsplash.com/photo-1593351415075-3bac9f45c877?auto=format&fit=crop&w=1600&q=80";
  }

  if (normalized.includes("rome")) {
    return "https://images.unsplash.com/photo-1529260830199-42c24126f198?auto=format&fit=crop&w=1600&q=80";
  }

  if (normalized.includes("athens")) {
    return "https://images.unsplash.com/photo-1555993539-1732b0258235?auto=format&fit=crop&w=1600&q=80";
  }

  if (destination) {
    return "https://images.unsplash.com/photo-1488646953014-85cb44e25828?auto=format&fit=crop&w=1600&q=80";
  }

  return "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=1400&q=80";
}

function AirportCode({
  code,
  align = "left",
  time,
}: {
  code: string;
  align?: "left" | "right";
  time?: string | null;
}) {
  return (
    <div className={cn("min-w-[4rem]", align === "right" && "text-right")}>
      <p className="font-display text-4xl leading-none">{code}</p>
      {time ? (
        <p className="mt-1 text-[11px] font-semibold uppercase tracking-[0.12em] text-white/72">
          {time}
        </p>
      ) : null}
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

function formatWeatherStatus(
  status: "ready" | "unavailable" | "not_requested" | null | undefined,
  forecastCount: number,
) {
  if (status === "ready" || forecastCount > 0) {
    return "Live";
  }
  if (status === "unavailable") {
    return "Pending";
  }
  if (status === "not_requested") {
    return "Off";
  }
  return "Open";
}

function formatPrimaryTemperature(forecast: WeatherDetail) {
  if (forecast.high_c == null && forecast.low_c == null) {
    return "—";
  }

  return `${Math.round(forecast.high_c ?? forecast.low_c ?? 0)}°`;
}

function splitHotelNotes(notes: string[]) {
  let tripadvisorUrl: string | null = null;
  let address: string | null = null;
  const highlights: string[] = [];

  for (const note of notes) {
    if (note.startsWith("TripAdvisor: ")) {
      tripadvisorUrl = note.replace("TripAdvisor: ", "").trim();
      continue;
    }

    if (!address && looksLikeAddress(note)) {
      address = note;
      continue;
    }

    highlights.push(note);
  }

  return {
    tripadvisorUrl,
    address,
    highlights,
  };
}

function formatCurrency(amount: number, currency: string | null | undefined) {
  return new Intl.NumberFormat("en-GB", {
    style: "currency",
    currency: (currency || "GBP").toUpperCase(),
    maximumFractionDigits: 0,
  }).format(amount);
}

function looksLikeAddress(value: string) {
  return /[0-9]/.test(value) || value.includes("Street") || value.includes("Avenue") || value.includes("Rua") || value.includes("Carrer") || value.includes("Pla");
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
