"use client";

import { CloudSun } from "lucide-react";

import type {
  ActivityDetail,
  HotelStayDetail,
  WeatherDetail,
} from "@/types/trip-draft";

export function WeatherCard({
  forecasts,
  status,
}: {
  forecasts: WeatherDetail[];
  status?: "ready" | "unavailable" | "not_requested" | null;
}) {
  const hasForecasts = forecasts.length > 0;
  const weatherCopy =
    forecasts[0]?.summary ||
    (status === "unavailable"
      ? "Live forecast opens closer to travel. Keep the plan flexible around the stated weather preference for now."
      : "Weather guidance will appear once the trip has dates or a live forecast window.");

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
          <p className="mt-1 text-sm text-foreground/60">{weatherCopy}</p>
        </div>
      </div>
      {hasForecasts ? (
        <div className="mt-5 grid grid-cols-2 gap-3 rounded-lg bg-white/55 px-4 py-3 sm:grid-cols-3">
          {forecasts.map((forecast) => (
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
  const heroImage = hotel.image_url;
  const pricingLabel =
    typeof hotel.nightly_rate_amount === "number"
      ? formatCurrency(hotel.nightly_rate_amount, hotel.nightly_rate_currency)
      : null;

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
          {pricingLabel ? (
            <p className="w-fit rounded-full border border-shell-border/70 bg-panel px-3 py-1.5 text-xs font-semibold text-foreground/70">
              {pricingLabel} nightly
            </p>
          ) : null}
          {hotel.address ? (
            <p className="text-sm leading-7 text-foreground/66">
              {hotel.address}
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

function formatTemperatureBand(high: number | null, low: number | null) {
  if (high == null && low == null) {
    return "Forecast pending";
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
    return "Too early";
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

function formatCurrency(amount: number, currency: string | null | undefined) {
  return new Intl.NumberFormat("en-GB", {
    style: "currency",
    currency: (currency || "GBP").toUpperCase(),
    maximumFractionDigits: 0,
  }).format(amount);
}
