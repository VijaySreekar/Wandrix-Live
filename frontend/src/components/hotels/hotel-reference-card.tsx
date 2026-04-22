"use client";

import { MoonStar } from "lucide-react";

import type { HotelStayDetail } from "@/types/trip-draft";


export function HotelReferenceCard({ hotel }: { hotel: HotelStayDetail }) {
  const details = splitHotelNotes(hotel.notes);
  const heroImage = hotel.image_url;

  return (
    <article className="overflow-hidden rounded-xl border border-shell-border bg-panel">
      <div
        className="h-32 border-b border-shell-border bg-cover bg-center"
        style={
          heroImage
            ? {
                backgroundImage: `linear-gradient(180deg, rgba(15,23,42,0.08), rgba(15,23,42,0.42)), url(${heroImage})`,
              }
            : {
                background:
                  "linear-gradient(145deg, #fbf7ee 0%, #f3ece1 100%)",
              }
        }
      >
        {!heroImage ? (
          <div className="flex h-full items-end px-4 py-3">
            <div>
              <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-[#8a7657]">
                Hotel image pending
              </p>
              <p className="mt-2 text-sm font-medium text-[#2c241a]">
                {hotel.area || "Stay details"}
              </p>
            </div>
          </div>
        ) : null}
      </div>
      <div className="border-b border-shell-border bg-[linear-gradient(135deg,color-mix(in_srgb,var(--accent)_10%,transparent),color-mix(in_srgb,var(--accent2)_12%,transparent))] px-4 py-4">
        <div className="flex items-start justify-between gap-3">
          <div className="min-w-0">
            <p className="text-base font-semibold leading-tight text-foreground">
              {hotel.hotel_name}
            </p>
            <p className="mt-1 text-sm text-foreground/60">
              {hotel.area ?? "Area still open"}
            </p>
          </div>
          <span className="shrink-0 rounded-md border border-shell-border bg-background px-2.5 py-1 text-[11px] font-medium text-foreground/62">
            Stay
          </span>
        </div>
      </div>

      <div className="space-y-4 px-4 py-4">
        <div className="grid gap-3 sm:grid-cols-[minmax(0,1fr)_auto] sm:items-center">
          <div className="flex items-start gap-3">
            <div className="mt-0.5 flex h-9 w-9 items-center justify-center rounded-lg bg-background text-[color:var(--accent)]">
              <MoonStar className="h-4 w-4" />
            </div>
            <div>
              <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-foreground/44">
                Stay window
              </p>
              <p className="mt-2 text-sm font-medium text-foreground">
                {formatStayWindow(hotel.check_in, hotel.check_out)}
              </p>
            </div>
          </div>
          {typeof hotel.nightly_rate_amount === "number" ? (
            <div className="rounded-lg border border-shell-border bg-background px-3 py-2.5 text-right">
              <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-foreground/44">
                Nightly
              </p>
              <p className="mt-1 text-sm font-semibold text-foreground">
                {formatCurrency(hotel.nightly_rate_amount, hotel.nightly_rate_currency)}
              </p>
            </div>
          ) : null}
        </div>

        <div className="grid gap-3">
          {details.highlights.length > 0 ? (
            <div className="grid gap-2">
              {details.highlights.map((note) => (
                <div
                  key={note}
                  className="rounded-lg border border-shell-border bg-background px-3 py-2.5 text-sm leading-6 text-foreground/68"
                >
                  {note}
                </div>
              ))}
            </div>
          ) : null}
        </div>
      </div>
    </article>
  );
}

function formatStayWindow(checkIn: string | null, checkOut: string | null) {
  return `${formatDateShort(checkIn)} through ${formatDateShort(checkOut)}`;
}

function formatDateShort(value: string | null) {
  if (!value) {
    return "TBD";
  }

  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) {
    return value;
  }

  return parsed.toLocaleDateString(undefined, {
    day: "numeric",
    month: "short",
    year: "numeric",
  });
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
