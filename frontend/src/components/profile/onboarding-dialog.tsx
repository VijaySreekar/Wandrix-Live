"use client";

import * as React from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { CheckCircle2, ChevronRight, Sparkles } from "lucide-react";

import { Button } from "@/components/ui/button";

type ProfileDefaults = {
  firstName?: string;
  lastName?: string;
  homeAirport?: string;
  homeCountry?: string;
  locationDecisionMade?: boolean;
};

type OnboardingDialogProps = {
  userId: string;
  initialEmail: string;
  initialDisplayName: string;
};

export function OnboardingDialog({
  userId,
}: OnboardingDialogProps) {
  const searchParams = useSearchParams();
  const storageKey = `wandrix:profile-defaults:${userId}`;
  const completionKey = `wandrix:profile-setup-complete:${userId}`;
  const onboardingTriggeredKey = `wandrix:onboarding-triggered:${userId}`;

  const [open, setOpen] = React.useState(false);
  const [missingFields, setMissingFields] = React.useState<string[]>([]);

  React.useEffect(() => {
    const shouldPrompt = searchParams.get("onboarding") === "1";
    if (!shouldPrompt) {
      return;
    }

    try {
      const alreadyComplete = window.localStorage.getItem(completionKey) === "true";
      const alreadyTriggered =
        window.sessionStorage.getItem(onboardingTriggeredKey) === "true";

      if (!alreadyComplete && !alreadyTriggered) {
        const stored = window.localStorage.getItem(storageKey);
        const parsed = stored ? (JSON.parse(stored) as ProfileDefaults) : {};
        const missing = getMissingFields(parsed);

        if (missing.length > 0) {
          const timeoutId = window.setTimeout(() => {
            setMissingFields(missing);
            setOpen(true);
          }, 0);

          window.sessionStorage.setItem(onboardingTriggeredKey, "true");

          const url = new URL(window.location.href);
          url.searchParams.delete("onboarding");
          window.history.replaceState({}, "", url.toString());

          return () => window.clearTimeout(timeoutId);
        }
      }
    } catch {
      // Ignore storage issues and avoid blocking chat.
    }

    const url = new URL(window.location.href);
    url.searchParams.delete("onboarding");
    window.history.replaceState({}, "", url.toString());
  }, [completionKey, onboardingTriggeredKey, searchParams, storageKey]);

  if (!open) {
    return null;
  }

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center px-4 py-8">
      <div className="absolute inset-0 bg-black/50 backdrop-blur-sm" />

      <div className="relative w-full max-w-[480px] rounded-2xl border border-shell-border bg-background p-6 shadow-[0_24px_60px_rgba(15,23,42,0.2)] sm:p-7">
        <div className="inline-flex h-12 w-12 items-center justify-center rounded-xl bg-[linear-gradient(135deg,var(--accent),var(--accent2))]">
          <Sparkles className="h-6 w-6 text-accent-foreground" />
        </div>

        <h2 className="mt-5 text-2xl font-semibold tracking-tight text-foreground">
          Finish your account setup
        </h2>
        <p className="mt-3 text-sm leading-7 text-foreground/68">
          Before Wandrix starts planning with your saved defaults, add the missing
          basics in your profile.
        </p>

        <div className="mt-5 rounded-xl border border-shell-border bg-shell p-4">
          <p className="text-sm font-medium text-foreground">Still missing</p>
          <ul className="mt-3 grid gap-2 text-sm text-foreground/68">
            {missingFields.map((field) => (
              <li key={field} className="flex items-center gap-2">
                <CheckCircle2 className="h-4 w-4 text-accent" />
                {field}
              </li>
            ))}
          </ul>
        </div>

        <div className="mt-6 flex flex-wrap items-center justify-between gap-3">
          <Button variant="ghost" type="button" onClick={() => setOpen(false)}>
            Skip for now
          </Button>
          <Button asChild>
            <Link href="/profile">
              Open profile
              <ChevronRight className="ml-1 h-4 w-4" />
            </Link>
          </Button>
        </div>
      </div>
    </div>
  );
}

function getMissingFields(profile: ProfileDefaults) {
  const missing: string[] = [];

  if (!profile.firstName?.trim()) {
    missing.push("First name");
  }
  if (!profile.lastName?.trim()) {
    missing.push("Last name");
  }
  if (!profile.homeAirport?.trim()) {
    missing.push("Home airport");
  }
  if (!profile.homeCountry?.trim()) {
    missing.push("Home country");
  }
  if (!profile.locationDecisionMade) {
    missing.push("Location choice");
  }

  return missing;
}
