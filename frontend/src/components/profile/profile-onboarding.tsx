"use client";

import Link from "next/link";
import * as React from "react";
import { useRouter } from "next/navigation";
import {
  CheckCircle2,
  ChevronRight,
  Globe,
  MapPin,
  PlaneTakeoff,
  SlidersHorizontal,
  Sparkles,
  UserRound,
} from "lucide-react";

import {
  Dialog,
  DialogClose,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/animate-ui/components/radix/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { createClient as createSupabaseBrowserClient } from "@/lib/supabase/client";
import { cn } from "@/lib/utils";

type TripPace = "easygoing" | "balanced" | "packed" | "";

type ProfileDefaults = {
  displayName: string;
  homeAirport: string;
  preferredCurrency: string;
  tripPace: TripPace;
  preferredStyles: string[];
  locationAssistEnabled: boolean;
  locationDecisionMade: boolean;
  locationSummary: string | null;
};

type ProfileOnboardingProps = {
  userId: string;
  initialEmail: string;
  initialDisplayName: string;
  nextPath: string;
};

type SetupSection = {
  id: string;
  title: string;
  description: string;
  summary: string;
  completed: boolean;
  actionLabel: string;
  dialog: React.ReactNode;
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

export function ProfileSettings({
  userId,
  initialEmail,
  initialDisplayName,
  nextPath,
}: ProfileOnboardingProps) {
  const router = useRouter();
  const supabase = React.useMemo(() => createSupabaseBrowserClient(), []);
  const storageKey = `wandrix:profile-defaults:${userId}`;
  const completionKey = `wandrix:profile-setup-complete:${userId}`;

  const [isHydrated, setIsHydrated] = React.useState(false);
  const [openSectionId, setOpenSectionId] = React.useState<string | null>("profile");
  const [profile, setProfile] = React.useState<ProfileDefaults>({
    displayName: initialDisplayName,
    homeAirport: "",
    preferredCurrency: "GBP",
    tripPace: "",
    preferredStyles: [],
    locationAssistEnabled: false,
    locationDecisionMade: false,
    locationSummary: null,
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
            displayName: parsed.displayName?.trim() || current.displayName,
          }));
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
      if (isProfileSetupComplete(profile)) {
        window.localStorage.setItem(completionKey, "true");
      }
    } catch {
      // Ignore localStorage write issues in unsupported/private contexts.
    }
  }, [completionKey, isHydrated, profile, storageKey]);

  const saveIdentity = React.useCallback(
    (displayName: string) => {
      setProfile((current) => ({
        ...current,
        displayName,
      }));

      void supabase.auth
        .updateUser({
          data: {
            full_name: displayName,
            name: displayName,
          },
        })
        .then(() => {
          router.refresh();
        })
        .catch(() => {
          // The local value is still preserved even if metadata sync fails.
        });
    },
    [router, supabase],
  );

  const sections = React.useMemo<SetupSection[]>(
    () => [
      {
        id: "profile",
        title: "Profile details",
        description:
          "Set the name Wandrix should use when it greets you and carries context across your trips.",
        summary: profile.displayName.trim() || "Name still not set",
        completed: Boolean(profile.displayName.trim()),
        actionLabel: profile.displayName.trim() ? "Edit profile" : "Add profile details",
        dialog: (
          <ProfileIdentityDialog
            triggerLabel={
              profile.displayName.trim() ? "Edit profile" : "Add profile details"
            }
            initialDisplayName={profile.displayName}
            initialEmail={initialEmail}
            onSave={saveIdentity}
          />
        ),
      },
      {
        id: "home-base",
        title: "Home airport and currency",
        description:
          "These become Wandrix's first assumptions when it opens a trip, but they should stay easy to override in chat.",
        summary:
          profile.homeAirport.trim() && profile.preferredCurrency
            ? `${profile.homeAirport.trim().toUpperCase()} • ${profile.preferredCurrency}`
            : "Departure defaults still not set",
        completed: Boolean(profile.homeAirport.trim() && profile.preferredCurrency),
        actionLabel: profile.homeAirport ? "Edit defaults" : "Set defaults",
        dialog: (
          <HomeBaseDialog
            triggerLabel={profile.homeAirport ? "Edit defaults" : "Set defaults"}
            initialCurrency={profile.preferredCurrency}
            initialHomeAirport={profile.homeAirport}
            onSave={(homeAirport, preferredCurrency) =>
              setProfile((current) => ({
                ...current,
                homeAirport,
                preferredCurrency,
              }))
            }
          />
        ),
      },
      {
        id: "preferences",
        title: "Travel preferences",
        description:
          "These are soft signals about how you usually like to travel. They should guide the assistant, not control the trip.",
        summary:
          profile.tripPace || profile.preferredStyles.length > 0
            ? [
                profile.tripPace || null,
                profile.preferredStyles.length > 0
                  ? profile.preferredStyles.join(", ")
                  : null,
              ]
                .filter(Boolean)
                .join(" • ")
            : "No soft preferences saved yet",
        completed: Boolean(profile.tripPace || profile.preferredStyles.length > 0),
        actionLabel:
          profile.tripPace || profile.preferredStyles.length > 0
            ? "Edit preferences"
            : "Set preferences",
        dialog: (
          <PreferencesDialog
            triggerLabel={
              profile.tripPace || profile.preferredStyles.length > 0
                ? "Edit preferences"
                : "Set preferences"
            }
            initialPace={profile.tripPace}
            initialStyles={profile.preferredStyles}
            onSave={(tripPace, preferredStyles) =>
              setProfile((current) => ({
                ...current,
                tripPace,
                preferredStyles,
              }))
            }
          />
        ),
      },
      {
        id: "location",
        title: "Location assistance",
        description:
          "Location should help with soft starting assumptions only. It should never silently override what you say in chat.",
        summary: profile.locationDecisionMade
          ? profile.locationAssistEnabled
            ? profile.locationSummary ?? "Enabled"
            : "Disabled"
          : "No decision saved yet",
        completed: profile.locationDecisionMade,
        actionLabel: profile.locationDecisionMade ? "Review location choice" : "Choose now",
        dialog: (
          <LocationAssistDialog
            triggerLabel={
              profile.locationDecisionMade ? "Review location choice" : "Choose now"
            }
            initialEnabled={profile.locationAssistEnabled}
            initialLocationSummary={profile.locationSummary}
            onSave={(locationAssistEnabled, locationSummary) =>
              setProfile((current) => ({
                ...current,
                locationAssistEnabled,
                locationDecisionMade: true,
                locationSummary,
              }))
            }
          />
        ),
      },
    ],
    [initialEmail, profile, saveIdentity],
  );

  const setupComplete = isProfileSetupComplete(profile);
  const completedCount = sections.filter((section) => section.completed).length;
  const firstIncompleteSection = sections.find((section) => !section.completed);
  const activeSectionId =
    openSectionId ?? firstIncompleteSection?.id ?? sections[0]?.id ?? null;

  if (!isHydrated) {
    return (
      <section className="rounded-xl border border-shell-border bg-shell p-6">
        <h1 className="text-xl font-semibold text-foreground">Loading account details</h1>
        <p className="mt-2 text-sm leading-7 text-foreground/68">
          Wandrix is pulling in your saved profile defaults.
        </p>
      </section>
    );
  }

  return setupComplete ? (
    <SettingsView
      initialEmail={initialEmail}
      nextPath={nextPath}
      profile={profile}
      sections={sections}
    />
  ) : (
    <SetupView
      completedCount={completedCount}
      nextPath={nextPath}
      openSectionId={activeSectionId}
      onOpenSection={setOpenSectionId}
      profile={profile}
      sections={sections}
    />
  );
}

function SetupView({
  completedCount,
  nextPath,
  openSectionId,
  onOpenSection,
  profile,
  sections,
}: {
  completedCount: number;
  nextPath: string;
  openSectionId: string | null;
  onOpenSection: React.Dispatch<React.SetStateAction<string | null>>;
  profile: ProfileDefaults;
  sections: SetupSection[];
}) {
  return (
    <section className="grid gap-4 xl:grid-cols-[minmax(0,1.08fr)_minmax(300px,0.92fr)]">
      <div className="rounded-xl border border-shell-border bg-shell p-5">
        <div className="flex flex-wrap items-start justify-between gap-4 border-b border-shell-border pb-4">
          <div>
            <h1 className="text-2xl font-semibold tracking-tight text-foreground">
              Finish your account setup
            </h1>
            <p className="mt-2 max-w-2xl text-sm leading-7 text-foreground/70">
              We only ask for the basics once. After this, the same page becomes a
              normal place to edit your profile and travel defaults.
            </p>
          </div>
          <ProgressRing completed={completedCount} total={sections.length} />
        </div>

        <div className="mt-4">
          {sections.map((section, index) => {
            const isOpen = openSectionId === section.id;

            return (
              <div
                key={section.id}
                className={cn(index > 0 && "border-t border-shell-border")}
              >
                <button
                  type="button"
                  onClick={() => onOpenSection(isOpen ? null : section.id)}
                  className="flex w-full items-start justify-between gap-4 px-1 py-4 text-left"
                >
                  <div className="flex min-w-0 gap-3">
                    <StepIndicator completed={section.completed} />
                    <div className="min-w-0">
                      <p
                        className={cn(
                          "text-sm font-semibold",
                          section.completed ? "text-accent" : "text-foreground",
                        )}
                      >
                        {section.title}
                      </p>
                      {isOpen ? (
                        <p className="mt-2 max-w-2xl text-sm leading-7 text-foreground/68">
                          {section.description}
                        </p>
                      ) : (
                        <p className="mt-1 text-sm text-foreground/56">
                          {section.summary}
                        </p>
                      )}
                    </div>
                  </div>
                  <ChevronRight
                    className={cn(
                      "mt-1 h-4 w-4 shrink-0 text-foreground/48 transition-transform",
                      isOpen && "rotate-90",
                    )}
                  />
                </button>

                {isOpen ? (
                  <div className="pb-4 pl-8 pr-1">{section.dialog}</div>
                ) : null}
              </div>
            );
          })}
        </div>

        <div className="mt-4 border-t border-shell-border pt-4">
          <ContinueToChatCard nextPath={nextPath} profile={profile} />
        </div>
      </div>

      <aside className="grid gap-4">
        <SummaryPanel profile={profile} />
        <UsageNotes />
      </aside>
    </section>
  );
}

function SettingsView({
  initialEmail,
  nextPath,
  profile,
  sections,
}: {
  initialEmail: string;
  nextPath: string;
  profile: ProfileDefaults;
  sections: SetupSection[];
}) {
  return (
    <section className="grid gap-4 xl:grid-cols-[minmax(0,1.1fr)_minmax(300px,0.9fr)]">
      <div className="rounded-xl border border-shell-border bg-shell p-5">
        <div className="flex flex-wrap items-start justify-between gap-4 border-b border-shell-border pb-4">
          <div>
            <h1 className="text-2xl font-semibold tracking-tight text-foreground">
              Profile and travel defaults
            </h1>
            <p className="mt-2 max-w-2xl text-sm leading-7 text-foreground/70">
              This page is here for edits now. Your account setup is already done,
              so these values simply help Wandrix start with better context.
            </p>
          </div>
          <Button asChild>
            <Link href={nextPath}>Open chat</Link>
          </Button>
        </div>

        <div className="mt-5 grid gap-3">
          <SettingsRow
            icon={UserRound}
            title="Profile details"
            summary={sections[0]?.summary ?? ""}
            description={`Signed-in email: ${initialEmail}`}
            action={sections[0]?.dialog ?? null}
          />
          <SettingsRow
            icon={PlaneTakeoff}
            title="Home airport and currency"
            summary={sections[1]?.summary ?? ""}
            description="Wandrix should start here unless the trip says otherwise."
            action={sections[1]?.dialog ?? null}
          />
          <SettingsRow
            icon={Sparkles}
            title="Travel preferences"
            summary={sections[2]?.summary ?? ""}
            description="These remain soft hints for the planner."
            action={sections[2]?.dialog ?? null}
          />
          <SettingsRow
            icon={MapPin}
            title="Location assistance"
            summary={sections[3]?.summary ?? ""}
            description="Optional assistance only, never a hard override."
            action={sections[3]?.dialog ?? null}
          />
        </div>
      </div>

      <aside className="grid gap-4">
        <SummaryPanel profile={profile} />
        <UsageNotes />
      </aside>
    </section>
  );
}

function ProfileIdentityDialog({
  triggerLabel,
  initialDisplayName,
  initialEmail,
  onSave,
}: {
  triggerLabel: string;
  initialDisplayName: string;
  initialEmail: string;
  onSave: (displayName: string) => void;
}) {
  const [displayName, setDisplayName] = React.useState(initialDisplayName);

  return (
    <Dialog>
      <DialogTrigger asChild>
        <Button>{triggerLabel}</Button>
      </DialogTrigger>
      <form
        onSubmit={(event) => {
          event.preventDefault();
          onSave(displayName.trim());
        }}
      >
        <DialogContent from="bottom" className="sm:max-w-[460px]">
          <DialogHeader>
            <DialogTitle>Edit profile</DialogTitle>
            <DialogDescription>
              Set the name Wandrix should use when it greets you and references
              your account.
            </DialogDescription>
          </DialogHeader>
          <div className="mt-5 grid gap-4">
            <div className="grid gap-2">
              <Label htmlFor="display-name">Full name</Label>
              <Input
                id="display-name"
                name="displayName"
                value={displayName}
                onChange={(event) => setDisplayName(event.target.value)}
                placeholder="How should Wandrix address you?"
              />
            </div>
            <div className="rounded-md border border-shell-border bg-panel px-3 py-3 text-sm text-foreground/68">
              Signed-in email: {initialEmail}
            </div>
          </div>
          <DialogFooter>
            <DialogClose asChild>
              <Button variant="outline" type="button">
                Cancel
              </Button>
            </DialogClose>
            <DialogClose asChild>
              <Button type="submit" disabled={!displayName.trim()}>
                Save profile
              </Button>
            </DialogClose>
          </DialogFooter>
        </DialogContent>
      </form>
    </Dialog>
  );
}

function HomeBaseDialog({
  triggerLabel,
  initialHomeAirport,
  initialCurrency,
  onSave,
}: {
  triggerLabel: string;
  initialHomeAirport: string;
  initialCurrency: string;
  onSave: (homeAirport: string, preferredCurrency: string) => void;
}) {
  const [homeAirport, setHomeAirport] = React.useState(initialHomeAirport);
  const [currency, setCurrency] = React.useState(initialCurrency);

  return (
    <Dialog>
      <DialogTrigger asChild>
        <Button>{triggerLabel}</Button>
      </DialogTrigger>
      <form
        onSubmit={(event) => {
          event.preventDefault();
          onSave(homeAirport.trim().toUpperCase(), currency);
        }}
      >
        <DialogContent from="bottom" className="sm:max-w-[460px]">
          <DialogHeader>
            <DialogTitle>Home airport and currency</DialogTitle>
            <DialogDescription>
              These become the first defaults in chat, not permanent rules for every
              trip.
            </DialogDescription>
          </DialogHeader>
          <div className="mt-5 grid gap-4">
            <div className="grid gap-2">
              <Label htmlFor="home-airport">Home airport</Label>
              <Input
                id="home-airport"
                name="homeAirport"
                value={homeAirport}
                onChange={(event) => setHomeAirport(event.target.value)}
                placeholder="LHR, MAN, DXB, JFK"
                maxLength={4}
              />
            </div>
            <div className="grid gap-2">
              <Label htmlFor="currency">Preferred currency</Label>
              <select
                id="currency"
                value={currency}
                onChange={(event) => setCurrency(event.target.value)}
                className="h-11 rounded-md border border-shell-border bg-background px-3 text-sm text-foreground outline-none transition focus:border-accent"
              >
                {CURRENCY_OPTIONS.map((option) => (
                  <option key={option} value={option}>
                    {option}
                  </option>
                ))}
              </select>
            </div>
          </div>
          <DialogFooter>
            <DialogClose asChild>
              <Button variant="outline" type="button">
                Cancel
              </Button>
            </DialogClose>
            <DialogClose asChild>
              <Button type="submit" disabled={!homeAirport.trim()}>
                Save defaults
              </Button>
            </DialogClose>
          </DialogFooter>
        </DialogContent>
      </form>
    </Dialog>
  );
}

function PreferencesDialog({
  triggerLabel,
  initialPace,
  initialStyles,
  onSave,
}: {
  triggerLabel: string;
  initialPace: TripPace;
  initialStyles: string[];
  onSave: (tripPace: TripPace, preferredStyles: string[]) => void;
}) {
  const [tripPace, setTripPace] = React.useState<TripPace>(initialPace);
  const [preferredStyles, setPreferredStyles] =
    React.useState<string[]>(initialStyles);

  function toggleStyle(style: string) {
    setPreferredStyles((current) =>
      current.includes(style)
        ? current.filter((item) => item !== style)
        : [...current, style],
    );
  }

  return (
    <Dialog>
      <DialogTrigger asChild>
        <Button>{triggerLabel}</Button>
      </DialogTrigger>
      <form
        onSubmit={(event) => {
          event.preventDefault();
          onSave(tripPace, preferredStyles);
        }}
      >
        <DialogContent from="bottom" className="sm:max-w-[520px]">
          <DialogHeader>
            <DialogTitle>Travel preferences</DialogTitle>
            <DialogDescription>
              Use this to nudge Wandrix in the right direction without making the
              planner rigid.
            </DialogDescription>
          </DialogHeader>
          <div className="mt-5 grid gap-5">
            <div className="grid gap-2">
              <Label>Trip pace</Label>
              <div className="flex flex-wrap gap-2">
                {PACE_OPTIONS.map((option) => (
                  <button
                    key={option.value}
                    type="button"
                    onClick={() => setTripPace(option.value)}
                    className={cn(
                      "rounded-md border px-3 py-2 text-sm transition-colors",
                      tripPace === option.value
                        ? "border-accent bg-accent-soft text-foreground"
                        : "border-shell-border bg-background text-foreground/72 hover:bg-panel",
                    )}
                  >
                    {option.label}
                  </button>
                ))}
              </div>
            </div>

            <div className="grid gap-2">
              <Label>Preferred trip styles</Label>
              <div className="flex flex-wrap gap-2">
                {STYLE_OPTIONS.map((style) => {
                  const active = preferredStyles.includes(style);
                  return (
                    <button
                      key={style}
                      type="button"
                      onClick={() => toggleStyle(style)}
                      className={cn(
                        "rounded-md border px-3 py-2 text-sm capitalize transition-colors",
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
            </div>
          </div>
          <DialogFooter>
            <DialogClose asChild>
              <Button variant="outline" type="button">
                Cancel
              </Button>
            </DialogClose>
            <DialogClose asChild>
              <Button type="submit">Save preferences</Button>
            </DialogClose>
          </DialogFooter>
        </DialogContent>
      </form>
    </Dialog>
  );
}

function LocationAssistDialog({
  triggerLabel,
  initialEnabled,
  initialLocationSummary,
  onSave,
}: {
  triggerLabel: string;
  initialEnabled: boolean;
  initialLocationSummary: string | null;
  onSave: (locationAssistEnabled: boolean, locationSummary: string | null) => void;
}) {
  const [enabled, setEnabled] = React.useState(initialEnabled);
  const [locationSummary, setLocationSummary] = React.useState<string | null>(
    initialLocationSummary,
  );
  const [isDetecting, setIsDetecting] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);

  async function detectLocation() {
    setError(null);
    if (!("geolocation" in navigator)) {
      setError("This browser does not support location detection.");
      return;
    }

    setIsDetecting(true);

    navigator.geolocation.getCurrentPosition(
      (position) => {
        const timezone = Intl.DateTimeFormat().resolvedOptions().timeZone;
        setEnabled(true);
        setLocationSummary(
          `Lat ${position.coords.latitude.toFixed(2)}, Lon ${position.coords.longitude.toFixed(2)} • ${timezone}`,
        );
        setIsDetecting(false);
      },
      (geoError) => {
        setError(geoError.message || "Location detection failed.");
        setIsDetecting(false);
      },
      { enableHighAccuracy: false, timeout: 10000, maximumAge: 600000 },
    );
  }

  return (
    <Dialog>
      <DialogTrigger asChild>
        <Button>{triggerLabel}</Button>
      </DialogTrigger>
      <DialogContent from="bottom" className="sm:max-w-[520px]">
        <DialogHeader>
          <DialogTitle>Location assistance</DialogTitle>
          <DialogDescription>
            Use location only to improve first assumptions. Your trip instructions
            should always take priority.
          </DialogDescription>
        </DialogHeader>
        <div className="mt-5 grid gap-4">
          <div className="rounded-md border border-shell-border bg-panel px-3 py-3 text-sm leading-7 text-foreground/70">
            This is optional. Wandrix should never silently replace a trip-specific
            departure point with whatever the browser reports.
          </div>

          {locationSummary ? (
            <div className="rounded-md border border-shell-border bg-background px-3 py-3 text-sm text-foreground/72">
              Saved assist context: {locationSummary}
            </div>
          ) : null}

          {error ? (
            <div className="rounded-md border border-shell-border bg-background px-3 py-3 text-sm text-foreground/72">
              {error}
            </div>
          ) : null}

          <div className="flex flex-wrap gap-2">
            <Button type="button" variant="outline" onClick={() => void detectLocation()}>
              {isDetecting ? "Detecting..." : "Use browser location"}
            </Button>
            <Button
              type="button"
              variant="ghost"
              onClick={() => {
                setEnabled(false);
                setLocationSummary(null);
              }}
            >
              Keep this off
            </Button>
          </div>
        </div>
        <DialogFooter>
          <DialogClose asChild>
            <Button variant="outline" type="button">
              Cancel
            </Button>
          </DialogClose>
          <DialogClose asChild>
            <Button type="button" onClick={() => onSave(enabled, locationSummary)}>
              Save location choice
            </Button>
          </DialogClose>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

function ContinueToChatCard({
  nextPath,
  profile,
}: {
  nextPath: string;
  profile: ProfileDefaults;
}) {
  const ready = isProfileSetupComplete(profile);

  return (
    <div className="rounded-lg border border-shell-border bg-panel p-4">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h2 className="text-base font-semibold text-foreground">Continue into chat</h2>
          <p className="mt-1 text-sm leading-7 text-foreground/68">
            Chat is still the main planning surface. This page only sets the
            account-level defaults it can start from.
          </p>
        </div>
        {ready ? (
          <CheckCircle2 className="mt-1 h-5 w-5 shrink-0 text-accent" />
        ) : null}
      </div>

      <div className="mt-4 flex flex-wrap gap-2">
        {ready ? (
          <Button asChild>
            <Link href={nextPath}>Open chat</Link>
          </Button>
        ) : (
          <Button disabled>Open chat</Button>
        )}
        {!ready ? (
          <p className="self-center text-sm text-foreground/60">
            Add your name, home airport, currency, and location choice first.
          </p>
        ) : null}
      </div>
    </div>
  );
}

function SummaryPanel({ profile }: { profile: ProfileDefaults }) {
  return (
    <div className="rounded-xl border border-shell-border bg-shell p-5">
      <h2 className="text-lg font-semibold text-foreground">Current defaults</h2>
      <p className="mt-2 text-sm leading-7 text-foreground/70">
        These are the values Wandrix should use for its starting context before the
        trip conversation takes over.
      </p>

      <div className="mt-4 grid gap-3">
        <SummaryRow
          icon={UserRound}
          label="Name"
          value={profile.displayName || "Still not set"}
        />
        <SummaryRow
          icon={PlaneTakeoff}
          label="Home airport"
          value={profile.homeAirport || "Still not set"}
        />
        <SummaryRow
          icon={Globe}
          label="Currency"
          value={profile.preferredCurrency || "Still not set"}
        />
        <SummaryRow
          icon={SlidersHorizontal}
          label="Travel pace"
          value={profile.tripPace || "Still not set"}
        />
        <SummaryRow
          icon={Sparkles}
          label="Preferred styles"
          value={
            profile.preferredStyles.length > 0
              ? profile.preferredStyles.join(", ")
              : "Still not set"
          }
        />
        <SummaryRow
          icon={MapPin}
          label="Location assistance"
          value={
            profile.locationDecisionMade
              ? profile.locationAssistEnabled
                ? profile.locationSummary ?? "Enabled"
                : "Disabled"
              : "Decision still pending"
          }
        />
      </div>
    </div>
  );
}

function UsageNotes() {
  return (
    <div className="rounded-xl border border-shell-border bg-shell p-5">
      <h2 className="text-lg font-semibold text-foreground">How Wandrix should use this</h2>
      <ul className="mt-3 grid gap-2 text-sm leading-7 text-foreground/70">
        <li className="rounded-md border border-shell-border bg-panel px-3 py-3">
          Start with the saved name in the greeting when possible.
        </li>
        <li className="rounded-md border border-shell-border bg-panel px-3 py-3">
          Use home airport and currency as the first assumption, but let the current
          trip override them immediately.
        </li>
        <li className="rounded-md border border-shell-border bg-panel px-3 py-3">
          Treat preferences as hints, not strict rules.
        </li>
        <li className="rounded-md border border-shell-border bg-panel px-3 py-3">
          If the user says something different in chat, the trip should follow the
          trip, not the profile.
        </li>
      </ul>
    </div>
  );
}

function SettingsRow({
  icon: Icon,
  title,
  summary,
  description,
  action,
}: {
  icon: React.ComponentType<{ className?: string }>;
  title: string;
  summary: string;
  description: string;
  action: React.ReactNode;
}) {
  return (
    <div className="flex flex-wrap items-start justify-between gap-4 rounded-lg border border-shell-border bg-panel p-4">
      <div className="flex min-w-0 gap-3">
        <span className="inline-flex h-9 w-9 shrink-0 items-center justify-center rounded-md border border-shell-border bg-background text-foreground/68">
          <Icon className="h-4 w-4" />
        </span>
        <div className="min-w-0">
          <p className="text-sm font-semibold text-foreground">{title}</p>
          <p className="mt-1 text-sm text-foreground/72">{summary}</p>
          <p className="mt-1 text-sm text-foreground/56">{description}</p>
        </div>
      </div>
      <div className="shrink-0">{action}</div>
    </div>
  );
}

function SummaryRow({
  icon: Icon,
  label,
  value,
}: {
  icon: React.ComponentType<{ className?: string }>;
  label: string;
  value: string;
}) {
  return (
    <div className="flex items-start gap-3 rounded-md border border-shell-border bg-panel px-3 py-3">
      <span className="mt-0.5 inline-flex h-8 w-8 items-center justify-center rounded-md bg-background text-foreground/70">
        <Icon className="h-4 w-4" />
      </span>
      <div>
        <p className="text-sm font-medium text-foreground">{label}</p>
        <p className="mt-1 text-sm leading-7 text-foreground/68">{value}</p>
      </div>
    </div>
  );
}

function ProgressRing({
  completed,
  total,
}: {
  completed: number;
  total: number;
}) {
  const progress = total > 0 ? (completed / total) * 100 : 0;
  const strokeDashoffset = 100 - progress;

  return (
    <div className="flex items-center gap-2 text-sm text-foreground/68">
      <svg className="-rotate-90" width="16" height="16" viewBox="0 0 16 16">
        <circle
          cx="8"
          cy="8"
          r="6"
          fill="none"
          pathLength="100"
          strokeWidth="2"
          className="stroke-shell-border"
        />
        <circle
          cx="8"
          cy="8"
          r="6"
          fill="none"
          pathLength="100"
          strokeWidth="2"
          strokeDasharray="100"
          strokeLinecap="round"
          className="stroke-accent"
          style={{ strokeDashoffset }}
        />
      </svg>
      <span>
        <strong className="text-foreground">{completed}</strong> / {total}
      </span>
    </div>
  );
}

function StepIndicator({ completed }: { completed: boolean }) {
  if (completed) {
    return <CheckCircle2 className="mt-0.5 h-5 w-5 shrink-0 text-accent" />;
  }

  return (
    <span className="mt-0.5 inline-flex h-5 w-5 shrink-0 rounded-full border border-shell-border bg-background" />
  );
}

function isProfileSetupComplete(profile: ProfileDefaults) {
  return Boolean(
    profile.displayName.trim() &&
      profile.homeAirport.trim() &&
      profile.preferredCurrency &&
      profile.locationDecisionMade,
  );
}
