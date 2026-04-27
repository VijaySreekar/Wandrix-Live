"use client";

import Image from "next/image";
import Link from "next/link";
import * as React from "react";
import { useRouter } from "next/navigation";
import {
  ChevronDown,
  Mail,
  MapPin,
  PlaneTakeoff,
  Sparkles,
  UserRound,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import BasicToast, {
  type ToastType,
} from "@/components/ui/smoothui/basic-toast";
import { createClient as createSupabaseBrowserClient } from "@/lib/supabase/client";
import { cn } from "@/lib/utils";

type TripPace = "easygoing" | "balanced" | "packed" | "";

type ProfileDefaults = {
  firstName: string;
  lastName: string;
  displayName: string;
  homeAirport: string;
  preferredCurrency: string;
  homeAddressLine1: string;
  homeAddressLine2: string;
  homeCity: string;
  homeRegion: string;
  homePostalCode: string;
  homeCountry: string;
  tripPace: TripPace;
  preferredStyles: string[];
  locationAssistEnabled: boolean;
  locationDecisionMade: boolean;
  locationSummary: string | null;
};

type ProfilePageViewProps = {
  userId: string;
  initialEmail: string;
  initialDisplayName: string;
  avatarUrl: string | null;
};

type ToastState = {
  visible: boolean;
  message: string;
  type: ToastType;
};

const STYLE_OPTIONS = [
  "culture",
  "food",
  "relaxed",
  "family",
  "romantic",
  "outdoors",
];

const PACE_OPTIONS: Array<{ value: Exclude<TripPace, "">; label: string }> = [
  { value: "easygoing", label: "Easygoing" },
  { value: "balanced", label: "Balanced" },
  { value: "packed", label: "Packed" },
];

const CURRENCY_OPTIONS = ["GBP", "EUR", "USD", "AED", "INR", "JPY", "AUD"];

export function ProfilePageView({
  userId,
  initialEmail,
  initialDisplayName,
  avatarUrl,
}: ProfilePageViewProps) {
  const router = useRouter();
  const supabase = React.useMemo(() => createSupabaseBrowserClient(), []);
  const storageKey = `wandrix:profile-defaults:${userId}`;

  const [isHydrated, setIsHydrated] = React.useState(false);
  const [isSavingIdentity, setIsSavingIdentity] = React.useState(false);
  const [isSavingDefaults, setIsSavingDefaults] = React.useState(false);
  const [isDetectingLocation, setIsDetectingLocation] = React.useState(false);
  const [locationError, setLocationError] = React.useState<string | null>(null);
  const [addressOpen, setAddressOpen] = React.useState(false);
  const [toast, setToast] = React.useState<ToastState>({
    visible: false,
    message: "",
    type: "success",
  });

  function showToast(message: string, type: ToastType = "success") {
    setToast({ visible: true, message, type });
  }

  const [profile, setProfile] = React.useState<ProfileDefaults>(() => {
    const { firstName, lastName } = splitInitialName(initialDisplayName);

    return {
      firstName,
      lastName,
      displayName: initialDisplayName,
      homeAirport: "",
      preferredCurrency: "GBP",
      homeAddressLine1: "",
      homeAddressLine2: "",
      homeCity: "",
      homeRegion: "",
      homePostalCode: "",
      homeCountry: "",
      tripPace: "",
      preferredStyles: [],
      locationAssistEnabled: false,
      locationDecisionMade: false,
      locationSummary: null,
    };
  });

  React.useEffect(() => {
    try {
      const stored = window.localStorage.getItem(storageKey);
      if (stored) {
        const parsed = JSON.parse(stored) as Partial<ProfileDefaults>;
        const timeoutId = window.setTimeout(() => {
          setProfile((current) => ({
            ...current,
            ...parsed,
            firstName: parsed.firstName?.trim() || current.firstName,
            lastName: parsed.lastName?.trim() || current.lastName,
            displayName:
              parsed.displayName?.trim() ||
              formatDisplayName(
                parsed.firstName?.trim() || current.firstName,
                parsed.lastName?.trim() || current.lastName,
              ) ||
              current.displayName,
          }));

          // Auto-expand address if any address field already has data
          const hasAddress = [
            parsed.homeAddressLine1,
            parsed.homeAddressLine2,
            parsed.homeCity,
            parsed.homeRegion,
            parsed.homePostalCode,
            parsed.homeCountry,
          ].some((v) => v?.trim());
          if (hasAddress) {
            setAddressOpen(true);
          }
        }, 0);

        return () => window.clearTimeout(timeoutId);
      }
    } catch {
      // Ignore malformed local profile data and keep defaults.
    } finally {
      setIsHydrated(true);
    }
  }, [storageKey]);

  React.useEffect(() => {
    if (!isHydrated) {
      return;
    }

    try {
      window.localStorage.setItem(storageKey, JSON.stringify(profile));
    } catch {
      // Ignore localStorage write issues in unsupported/private contexts.
    }
  }, [isHydrated, profile, storageKey]);

  const displayName =
    profile.displayName.trim() ||
    formatDisplayName(profile.firstName, profile.lastName) ||
    "Traveler";
  const initials = displayName
    .split(" ")
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase())
    .join("");

  function updateProfile<K extends keyof ProfileDefaults>(
    field: K,
    value: ProfileDefaults[K],
  ) {
    setProfile((current) => {
      const next = { ...current, [field]: value };

      if (field === "firstName" || field === "lastName") {
        next.displayName =
          formatDisplayName(
            field === "firstName" ? String(value) : next.firstName,
            field === "lastName" ? String(value) : next.lastName,
          ) || current.displayName;
      }

      return next;
    });
  }

  function toggleStyle(style: string) {
    setProfile((current) => ({
      ...current,
      preferredStyles: current.preferredStyles.includes(style)
        ? current.preferredStyles.filter((item) => item !== style)
        : [...current.preferredStyles, style],
    }));
  }

  async function handleIdentitySave(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setIsSavingIdentity(true);

    const fullName =
      formatDisplayName(profile.firstName, profile.lastName) ||
      profile.displayName.trim() ||
      "Traveler";

    try {
      const { error } = await supabase.auth.updateUser({
        data: {
          first_name: profile.firstName.trim(),
          last_name: profile.lastName.trim(),
          full_name: fullName,
          name: fullName,
        },
      });

      if (error) {
        throw error;
      }

      setProfile((current) => ({ ...current, displayName: fullName }));
      showToast("Profile details saved.");
      router.refresh();
    } catch (caughtError) {
      showToast(
        caughtError instanceof Error
          ? caughtError.message
          : "Could not save profile details.",
        "error",
      );
    } finally {
      setIsSavingIdentity(false);
    }
  }

  async function handleDefaultsSave(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setIsSavingDefaults(true);

    try {
      setProfile((current) => ({
        ...current,
        homeAirport: current.homeAirport.trim().toUpperCase(),
        homeAddressLine1: current.homeAddressLine1.trim(),
        homeAddressLine2: current.homeAddressLine2.trim(),
        homeCity: current.homeCity.trim(),
        homeRegion: current.homeRegion.trim(),
        homePostalCode: current.homePostalCode.trim(),
        homeCountry: current.homeCountry.trim(),
      }));
      showToast("Travel defaults saved.");
    } finally {
      setIsSavingDefaults(false);
    }
  }

  async function detectLocation() {
    setLocationError(null);

    if (!("geolocation" in navigator)) {
      setLocationError("This browser does not support location detection.");
      return;
    }

    setIsDetectingLocation(true);

    navigator.geolocation.getCurrentPosition(
      (position) => {
        const timezone = Intl.DateTimeFormat().resolvedOptions().timeZone;
        setProfile((current) => ({
          ...current,
          locationAssistEnabled: true,
          locationDecisionMade: true,
          locationSummary: `Lat ${position.coords.latitude.toFixed(2)}, Lon ${position.coords.longitude.toFixed(2)} · ${timezone}`,
        }));
        showToast("Location detected and saved.");
        setIsDetectingLocation(false);
      },
      (geoError) => {
        setLocationError(geoError.message || "Location detection failed.");
        setIsDetectingLocation(false);
      },
      { enableHighAccuracy: false, timeout: 10000, maximumAge: 600000 },
    );
  }

  if (!isHydrated) {
    return (
      <div className="mx-auto max-w-2xl px-4 py-10">
        <div className="rounded-xl border border-shell-border bg-shell p-6">
          <p className="text-sm text-foreground/68">Loading profile...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-2xl px-4 py-8 sm:py-10">
      <BasicToast
        message={toast.message}
        type={toast.type}
        isVisible={toast.visible}
        duration={3000}
        onClose={() => setToast((t) => ({ ...t, visible: false }))}
      />

      {/* ── Header ── */}
      <div className="flex flex-col gap-5 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-center gap-4">
          <AvatarBlock
            avatarUrl={avatarUrl}
            displayName={displayName}
            initials={initials || "W"}
          />
          <div>
            <h1 className="text-2xl font-semibold tracking-tight text-foreground">
              {displayName}
            </h1>
            <p className="mt-1 flex items-center gap-1.5 text-sm text-foreground/56">
              <Mail className="h-3.5 w-3.5" />
              {initialEmail}
            </p>
          </div>
        </div>
        <Button variant="outline" asChild>
          <Link href="/chat">Open chat</Link>
        </Button>
      </div>

      {/* ── Profile details ── */}
      <form className="mt-8" onSubmit={handleIdentitySave}>
        <SectionLabel icon={UserRound} title="Profile details" />

        <div className="mt-4 grid gap-4 sm:grid-cols-2">
          <Field>
            <Label htmlFor="profile-first-name">First name</Label>
            <Input
              id="profile-first-name"
              value={profile.firstName}
              onChange={(e) => updateProfile("firstName", e.target.value)}
              placeholder="Vijay"
            />
          </Field>
          <Field>
            <Label htmlFor="profile-last-name">Last name</Label>
            <Input
              id="profile-last-name"
              value={profile.lastName}
              onChange={(e) => updateProfile("lastName", e.target.value)}
              placeholder="Sreekar"
            />
          </Field>
        </div>

        <div className="mt-4 flex items-center justify-end">
          <Button type="submit" disabled={isSavingIdentity}>
            {isSavingIdentity ? "Saving..." : "Save profile"}
          </Button>
        </div>
      </form>

      <Divider />

      {/* ── Home base ── */}
      <form onSubmit={handleDefaultsSave}>
        <SectionLabel icon={PlaneTakeoff} title="Home base" />

        <div className="mt-4 grid gap-4 sm:grid-cols-2">
          <Field>
            <Label htmlFor="profile-home-airport">Home airport</Label>
            <Input
              id="profile-home-airport"
              maxLength={4}
              value={profile.homeAirport}
              onChange={(e) => updateProfile("homeAirport", e.target.value)}
              placeholder="LHR"
            />
          </Field>
          <Field>
            <Label htmlFor="profile-currency">Currency</Label>
            <select
              id="profile-currency"
              value={profile.preferredCurrency}
              onChange={(e) =>
                updateProfile("preferredCurrency", e.target.value)
              }
              className="h-11 rounded-md border border-shell-border bg-background px-3 text-sm text-foreground outline-none transition focus:border-accent"
            >
              {CURRENCY_OPTIONS.map((opt) => (
                <option key={opt} value={opt}>
                  {opt}
                </option>
              ))}
            </select>
          </Field>
          <Field>
            <Label htmlFor="profile-country">Country</Label>
            <Input
              id="profile-country"
              value={profile.homeCountry}
              onChange={(e) => updateProfile("homeCountry", e.target.value)}
              placeholder="United Kingdom"
            />
          </Field>
          <Field>
            <Label htmlFor="profile-city">City</Label>
            <Input
              id="profile-city"
              value={profile.homeCity}
              onChange={(e) => updateProfile("homeCity", e.target.value)}
              placeholder="London"
            />
          </Field>
        </div>

        {/* Collapsible address details */}
        <button
          type="button"
          onClick={() => setAddressOpen((o) => !o)}
          className="mt-3 flex items-center gap-1.5 text-sm font-medium text-foreground/56 transition-colors hover:text-foreground/80"
        >
          <ChevronDown
            className={cn(
              "h-4 w-4 transition-transform",
              addressOpen && "rotate-180",
            )}
          />
          {addressOpen ? "Hide full address" : "Add full address"}
        </button>

        {addressOpen && (
          <div className="mt-3 grid gap-4 sm:grid-cols-2">
            <Field className="sm:col-span-2">
              <Label htmlFor="profile-address-1">Address line 1</Label>
              <Input
                id="profile-address-1"
                value={profile.homeAddressLine1}
                onChange={(e) =>
                  updateProfile("homeAddressLine1", e.target.value)
                }
                placeholder="221B Baker Street"
              />
            </Field>
            <Field className="sm:col-span-2">
              <Label htmlFor="profile-address-2">Address line 2</Label>
              <Input
                id="profile-address-2"
                value={profile.homeAddressLine2}
                onChange={(e) =>
                  updateProfile("homeAddressLine2", e.target.value)
                }
                placeholder="Apartment, building, etc."
              />
            </Field>
            <Field>
              <Label htmlFor="profile-region">State / region</Label>
              <Input
                id="profile-region"
                value={profile.homeRegion}
                onChange={(e) => updateProfile("homeRegion", e.target.value)}
                placeholder="Greater London"
              />
            </Field>
            <Field>
              <Label htmlFor="profile-postal-code">Postal code</Label>
              <Input
                id="profile-postal-code"
                value={profile.homePostalCode}
                onChange={(e) =>
                  updateProfile("homePostalCode", e.target.value)
                }
                placeholder="NW1 6XE"
              />
            </Field>
          </div>
        )}

        <div className="mt-4 flex items-center justify-end">
          <Button type="submit" disabled={isSavingDefaults}>
            {isSavingDefaults ? "Saving..." : "Save home base"}
          </Button>
        </div>
      </form>

      <Divider />

      {/* ── Travel preferences ── */}
      <div>
        <SectionLabel icon={Sparkles} title="Travel preferences" />
        <p className="mt-1 text-sm text-foreground/56">
          Soft hints — the trip conversation always takes priority.
        </p>

        <div className="mt-4 grid gap-4">
          <Field>
            <Label>Trip pace</Label>
            <div className="flex flex-wrap gap-2">
              {PACE_OPTIONS.map((option) => (
                <button
                  key={option.value}
                  type="button"
                  onClick={() => updateProfile("tripPace", option.value)}
                  className={cn(
                    "rounded-lg border px-3.5 py-2 text-sm transition-colors",
                    profile.tripPace === option.value
                      ? "border-accent bg-accent-soft text-foreground"
                      : "border-shell-border bg-background text-foreground/72 hover:bg-panel",
                  )}
                >
                  {option.label}
                </button>
              ))}
            </div>
          </Field>

          <Field>
            <Label>Styles</Label>
            <div className="flex flex-wrap gap-2">
              {STYLE_OPTIONS.map((style) => {
                const active = profile.preferredStyles.includes(style);
                return (
                  <button
                    key={style}
                    type="button"
                    onClick={() => toggleStyle(style)}
                    className={cn(
                      "rounded-lg border px-3.5 py-2 text-sm capitalize transition-colors",
                      active
                        ? "border-accent bg-accent-soft text-foreground"
                        : "border-shell-border bg-background text-foreground/72 hover:bg-panel",
                    )}
                  >
                    {style}
                  </button>
                );
              })}
            </div>
          </Field>
        </div>
      </div>

      <Divider />

      {/* ── Location ── */}
      <div>
        <SectionLabel icon={MapPin} title="Location assistance" />
        <p className="mt-1 text-sm text-foreground/56">
          Optional — helps with initial assumptions, never overrides the trip.
        </p>

        <div className="mt-4 flex flex-wrap items-center gap-2">
          <button
            type="button"
            onClick={() =>
              setProfile((c) => ({
                ...c,
                locationAssistEnabled: true,
                locationDecisionMade: true,
              }))
            }
            className={cn(
              "rounded-lg border px-3.5 py-2 text-sm transition-colors",
              profile.locationAssistEnabled
                ? "border-accent bg-accent-soft text-foreground"
                : "border-shell-border bg-background text-foreground/72 hover:bg-panel",
            )}
          >
            Enabled
          </button>
          <button
            type="button"
            onClick={() =>
              setProfile((c) => ({
                ...c,
                locationAssistEnabled: false,
                locationDecisionMade: true,
                locationSummary: null,
              }))
            }
            className={cn(
              "rounded-lg border px-3.5 py-2 text-sm transition-colors",
              !profile.locationAssistEnabled && profile.locationDecisionMade
                ? "border-accent bg-accent-soft text-foreground"
                : "border-shell-border bg-background text-foreground/72 hover:bg-panel",
            )}
          >
            Disabled
          </button>
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={() => void detectLocation()}
            disabled={isDetectingLocation}
          >
            {isDetectingLocation ? "Detecting..." : "Detect location"}
          </Button>
        </div>

        {profile.locationSummary && profile.locationAssistEnabled && (
          <p className="mt-3 text-sm text-foreground/60">
            {profile.locationSummary}
          </p>
        )}

        {locationError && (
          <p className="mt-3 text-sm text-foreground/60">{locationError}</p>
        )}
      </div>

      <div className="pb-8" />
    </div>
  );
}

/* ─── Shared pieces ─── */

function AvatarBlock({
  avatarUrl,
  displayName,
  initials,
}: {
  avatarUrl: string | null;
  displayName: string;
  initials: string;
}) {
  if (avatarUrl) {
    return (
      <Image
        alt={displayName}
        src={avatarUrl}
        width={72}
        height={72}
        className="h-[72px] w-[72px] rounded-2xl object-cover shadow-sm"
      />
    );
  }

  return (
    <span className="inline-flex h-[72px] w-[72px] items-center justify-center rounded-2xl bg-[linear-gradient(135deg,var(--accent),var(--accent2))] text-xl font-semibold text-accent-foreground shadow-sm">
      {initials}
    </span>
  );
}

function SectionLabel({
  icon: Icon,
  title,
}: {
  icon: React.ComponentType<{ className?: string }>;
  title: string;
}) {
  return (
    <div className="flex items-center gap-2.5">
      <Icon className="h-[18px] w-[18px] text-foreground/48" />
      <h2 className="text-base font-semibold text-foreground">{title}</h2>
    </div>
  );
}

function Divider() {
  return <hr className="my-8 border-shell-border" />;
}

function Field({
  children,
  className,
}: {
  children: React.ReactNode;
  className?: string;
}) {
  return <div className={cn("grid gap-2", className)}>{children}</div>;
}

function splitInitialName(name: string) {
  const [firstName = "", ...rest] = name.trim().split(/\s+/);
  return {
    firstName,
    lastName: rest.join(" "),
  };
}

function formatDisplayName(firstName: string, lastName: string) {
  return [firstName.trim(), lastName.trim()].filter(Boolean).join(" ").trim();
}
