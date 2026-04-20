"use client";

import { useEffect, useState } from "react";
import { MapPinned } from "lucide-react";

import { Input } from "@/components/ui/input";
import { searchProviderLocations } from "@/lib/api/providers";
import { cn } from "@/lib/utils";
import type {
  PlannerLocationSuggestion,
  PlannerLocationSuggestionKind,
} from "@/types/location-suggestions";

type RouteLocationInputProps = {
  accessToken?: string;
  disabled: boolean;
  kind: PlannerLocationSuggestionKind;
  label: string;
  onChange: (value: string | null) => void;
  placeholder: string;
  value: string;
};

const INPUT_CLASSNAME =
  "h-11 rounded-lg border border-[var(--planner-board-border)] bg-white/50 px-4 text-[var(--planner-board-text)] placeholder:text-[var(--planner-board-muted-strong)] transition-all duration-200 focus-visible:border-[var(--planner-board-cta)] focus-visible:ring-2 focus-visible:ring-[color:color-mix(in_srgb,var(--planner-board-cta)_20%,transparent)] focus-visible:bg-white";

export function RouteLocationInput({
  accessToken,
  disabled,
  kind,
  label,
  onChange,
  placeholder,
  value,
}: RouteLocationInputProps) {
  const [isFocused, setIsFocused] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [suggestions, setSuggestions] = useState<PlannerLocationSuggestion[]>([]);

  useEffect(() => {
    const query = value.trim();

    if (!isFocused || query.length < 2 || !accessToken) {
      return;
    }

    const controller = new AbortController();
    const timeout = window.setTimeout(async () => {
      setIsLoading(true);

      try {
        const response = await searchProviderLocations(
          query,
          kind,
          accessToken,
          controller.signal,
        );
        setSuggestions(response.items);
      } catch {
        setSuggestions([]);
      } finally {
        setIsLoading(false);
      }
    }, 180);

    return () => {
      controller.abort();
      window.clearTimeout(timeout);
    };
  }, [accessToken, isFocused, kind, value]);

  const showSuggestions = isFocused && suggestions.length > 0;

  return (
    <div className="relative rounded-[1.35rem] border border-[var(--planner-board-border)] bg-[var(--planner-board-card)] p-4 shadow-[0_4px_12px_rgba(0,0,0,0.03)]">
      <div className="mb-3 flex items-center gap-2">
        <span className="inline-flex size-8 items-center justify-center rounded-full bg-[var(--planner-board-soft)] text-[var(--planner-board-accent-text)]">
          <MapPinned className="size-4" />
        </span>
        <p className="text-[11px] font-semibold uppercase tracking-[0.08em] text-[var(--planner-board-muted-strong)]">
          {label}
        </p>
      </div>

      <div className="relative">
        <Input
          disabled={disabled}
          placeholder={placeholder}
          value={value}
          onFocus={() => {
            setIsFocused(true);
            if (value.trim().length < 2) {
              setSuggestions([]);
            }
          }}
          onBlur={() => {
            window.setTimeout(() => setIsFocused(false), 120);
          }}
          onChange={(event) => {
            const nextValue = event.target.value || null;
            if ((nextValue ?? "").trim().length < 2) {
              setSuggestions([]);
              setIsLoading(false);
            }
            onChange(nextValue);
          }}
          className={cn(INPUT_CLASSNAME, "bg-[var(--planner-board-soft)]")}
        />

        {isFocused && isLoading ? (
          <div className="absolute left-0 right-0 top-[calc(100%+0.5rem)] z-20 rounded-[1rem] border border-[var(--planner-board-border)] bg-[var(--planner-board-card)] px-4 py-3 shadow-[0_18px_36px_rgba(0,0,0,0.08)]">
            <p className="text-sm text-[var(--planner-board-muted)]">
              Searching places...
            </p>
          </div>
        ) : null}

        {showSuggestions ? (
          <div className="absolute left-0 right-0 top-[calc(100%+0.5rem)] z-20 overflow-hidden rounded-[1rem] border border-[var(--planner-board-border)] bg-[var(--planner-board-card)] shadow-[0_18px_36px_rgba(0,0,0,0.08)]">
            <div className="max-h-72 overflow-y-auto p-2">
              {suggestions.map((suggestion) => (
                <button
                  key={suggestion.id}
                  type="button"
                  onMouseDown={(event) => {
                    event.preventDefault();
                    onChange(suggestion.label);
                    setSuggestions([]);
                    setIsFocused(false);
                  }}
                  className="flex w-full items-start rounded-xl px-3 py-2.5 text-left transition-colors hover:bg-[var(--planner-board-soft)]"
                >
                  <div>
                    <p className="text-sm font-medium text-[var(--planner-board-text)]">
                      {suggestion.label}
                    </p>
                    {suggestion.detail ? (
                      <p className="mt-0.5 text-xs text-[var(--planner-board-muted)]">
                        {suggestion.detail}
                      </p>
                    ) : null}
                  </div>
                </button>
              ))}
            </div>
          </div>
        ) : null}
      </div>
    </div>
  );
}
