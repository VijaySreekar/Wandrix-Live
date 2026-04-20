"use client";

import { ExternalLink, MapPin, MoonStar } from "lucide-react";

import type { HotelStayDetail } from "@/types/trip-draft";


export function HotelReferenceCard({ hotel }: { hotel: HotelStayDetail }) {
  const details = splitHotelNotes(hotel.notes);

  return (
    <article className="overflow-hidden rounded-xl border border-shell-border bg-panel">
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
          {details.tripadvisorUrl ? (
            <a
              href={details.tripadvisorUrl}
              target="_blank"
              rel="noreferrer"
              className="inline-flex items-center gap-2 rounded-md border border-shell-border bg-background px-3 py-2 text-sm font-medium text-foreground transition-colors hover:bg-panel-strong"
            >
              Source
              <ExternalLink className="h-4 w-4 text-foreground/56" />
            </a>
          ) : null}
        </div>

        <div className="grid gap-3">
          {details.address ? (
            <div className="rounded-lg border border-shell-border bg-background px-3 py-3">
              <div className="flex items-start gap-3">
                <MapPin className="mt-0.5 h-4 w-4 shrink-0 text-[color:var(--accent)]" />
                <div>
                  <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-foreground/44">
                    Address
                  </p>
                  <p className="mt-1 text-sm leading-6 text-foreground/70">
                    {details.address}
                  </p>
                </div>
              </div>
            </div>
          ) : null}

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

function looksLikeAddress(value: string) {
  return /[0-9]/.test(value) || value.includes("Street") || value.includes("Avenue") || value.includes("Rua") || value.includes("Carrer") || value.includes("Pla");
}
