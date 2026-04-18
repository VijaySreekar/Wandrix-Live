"use client";

import { useState } from "react";

import type { TravelPackageRequest, TravelPace } from "@/types/package";


type PackageFormProps = {
  onSubmit: (payload: TravelPackageRequest) => Promise<void>;
  isLoading: boolean;
};


type FormState = {
  origin: string;
  destination: string;
  startDate: string;
  endDate: string;
  adults: string;
  children: string;
  budget: string;
  interests: string;
  pace: TravelPace;
  includeFlights: boolean;
  includeHotel: boolean;
};


const initialState: FormState = {
  origin: "London",
  destination: "Tokyo",
  startDate: "2026-05-01",
  endDate: "2026-05-06",
  adults: "2",
  children: "0",
  budget: "2400",
  interests: "food, culture, hidden spots",
  pace: "balanced",
  includeFlights: true,
  includeHotel: true,
};


export function PackageForm({ onSubmit, isLoading }: PackageFormProps) {
  const [form, setForm] = useState<FormState>(initialState);

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();

    const payload: TravelPackageRequest = {
      origin: form.origin.trim(),
      destination: form.destination.trim(),
      start_date: form.startDate,
      end_date: form.endDate,
      travelers: {
        adults: Number(form.adults),
        children: Number(form.children),
      },
      budget_gbp: form.budget ? Number(form.budget) : undefined,
      interests: form.interests
        .split(",")
        .map((item) => item.trim())
        .filter(Boolean),
      pace: form.pace,
      include_flights: form.includeFlights,
      include_hotel: form.includeHotel,
    };

    await onSubmit(payload);
  }

  function updateField<K extends keyof FormState>(key: K, value: FormState[K]) {
    setForm((current) => ({ ...current, [key]: value }));
  }

  return (
    <form className="grid gap-4" onSubmit={handleSubmit}>
      <div className="grid gap-4 md:grid-cols-2">
        <label className="grid gap-2 text-sm text-foreground/80">
          Origin
          <input
            className="rounded-2xl border border-panel-border bg-white/90 px-4 py-3 outline-none transition focus:border-accent"
            value={form.origin}
            onChange={(event) => updateField("origin", event.target.value)}
            required
          />
        </label>

        <label className="grid gap-2 text-sm text-foreground/80">
          Destination
          <input
            className="rounded-2xl border border-panel-border bg-white/90 px-4 py-3 outline-none transition focus:border-accent"
            value={form.destination}
            onChange={(event) => updateField("destination", event.target.value)}
            required
          />
        </label>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <label className="grid gap-2 text-sm text-foreground/80">
          Start date
          <input
            type="date"
            className="rounded-2xl border border-panel-border bg-white/90 px-4 py-3 outline-none transition focus:border-accent"
            value={form.startDate}
            onChange={(event) => updateField("startDate", event.target.value)}
            required
          />
        </label>

        <label className="grid gap-2 text-sm text-foreground/80">
          End date
          <input
            type="date"
            className="rounded-2xl border border-panel-border bg-white/90 px-4 py-3 outline-none transition focus:border-accent"
            value={form.endDate}
            onChange={(event) => updateField("endDate", event.target.value)}
            required
          />
        </label>
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        <label className="grid gap-2 text-sm text-foreground/80">
          Adults
          <input
            type="number"
            min="1"
            className="rounded-2xl border border-panel-border bg-white/90 px-4 py-3 outline-none transition focus:border-accent"
            value={form.adults}
            onChange={(event) => updateField("adults", event.target.value)}
            required
          />
        </label>

        <label className="grid gap-2 text-sm text-foreground/80">
          Children
          <input
            type="number"
            min="0"
            className="rounded-2xl border border-panel-border bg-white/90 px-4 py-3 outline-none transition focus:border-accent"
            value={form.children}
            onChange={(event) => updateField("children", event.target.value)}
          />
        </label>

        <label className="grid gap-2 text-sm text-foreground/80">
          Budget in GBP
          <input
            type="number"
            min="0"
            step="100"
            className="rounded-2xl border border-panel-border bg-white/90 px-4 py-3 outline-none transition focus:border-accent"
            value={form.budget}
            onChange={(event) => updateField("budget", event.target.value)}
          />
        </label>
      </div>

      <div className="grid gap-4 md:grid-cols-[1fr_220px]">
        <label className="grid gap-2 text-sm text-foreground/80">
          Interests
          <input
            className="rounded-2xl border border-panel-border bg-white/90 px-4 py-3 outline-none transition focus:border-accent"
            value={form.interests}
            onChange={(event) => updateField("interests", event.target.value)}
            placeholder="food, beaches, museums"
          />
        </label>

        <label className="grid gap-2 text-sm text-foreground/80">
          Pace
          <select
            className="rounded-2xl border border-panel-border bg-white/90 px-4 py-3 outline-none transition focus:border-accent"
            value={form.pace}
            onChange={(event) => updateField("pace", event.target.value as TravelPace)}
          >
            <option value="relaxed">Relaxed</option>
            <option value="balanced">Balanced</option>
            <option value="packed">Packed</option>
          </select>
        </label>
      </div>

      <div className="flex flex-wrap gap-3 text-sm text-foreground/80">
        <label className="flex items-center gap-2 rounded-full border border-panel-border bg-white/75 px-4 py-2">
          <input
            type="checkbox"
            checked={form.includeFlights}
            onChange={(event) => updateField("includeFlights", event.target.checked)}
          />
          Include flights
        </label>

        <label className="flex items-center gap-2 rounded-full border border-panel-border bg-white/75 px-4 py-2">
          <input
            type="checkbox"
            checked={form.includeHotel}
            onChange={(event) => updateField("includeHotel", event.target.checked)}
          />
          Include hotel
        </label>
      </div>

      <button
        type="submit"
        disabled={isLoading}
        className="mt-2 inline-flex items-center justify-center rounded-full bg-accent px-6 py-3 font-semibold text-white transition hover:bg-accent-strong disabled:cursor-not-allowed disabled:opacity-70"
      >
        {isLoading ? "Generating package..." : "Generate travel package"}
      </button>
    </form>
  );
}
