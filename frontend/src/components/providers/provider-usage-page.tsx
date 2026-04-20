"use client";

import { useEffect, useMemo, useState } from "react";

import { getProviderStatuses, getProviderUsage } from "@/lib/api/providers";
import { createClient as createSupabaseBrowserClient } from "@/lib/supabase/client";
import type { ProviderStatusItem } from "@/types/provider-status";
import type { ProviderUsageItem } from "@/types/provider-usage";


type ProviderUsagePageProps = {
  title?: string;
};

export function ProviderUsagePage({
  title = "Provider usage",
}: ProviderUsagePageProps) {
  const [usageItems, setUsageItems] = useState<ProviderUsageItem[]>([]);
  const [statusItems, setStatusItems] = useState<ProviderStatusItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function loadData() {
      setIsLoading(true);
      setError(null);

      try {
        const supabase = createSupabaseBrowserClient();
        const {
          data: { session },
          error: sessionError,
        } = await supabase.auth.getSession();

        if (sessionError || !session?.access_token) {
          throw new Error("Sign in to inspect provider usage.");
        }

        const [usageResponse, statusResponse] = await Promise.all([
          getProviderUsage(session.access_token),
          getProviderStatuses(session.access_token),
        ]);

        if (!cancelled) {
          setUsageItems(usageResponse.items);
          setStatusItems(statusResponse.items);
        }
      } catch (caughtError) {
        if (!cancelled) {
          setError(
            caughtError instanceof Error
              ? caughtError.message
              : "Could not load provider usage right now.",
          );
        }
      } finally {
        if (!cancelled) {
          setIsLoading(false);
        }
      }
    }

    void loadData();

    return () => {
      cancelled = true;
    };
  }, []);

  const usageByProvider = useMemo(
    () => new Map(usageItems.map((item) => [item.provider, item])),
    [usageItems],
  );

  return (
    <section className="mx-auto flex w-full max-w-[1200px] flex-col gap-4 px-3 py-4 sm:px-4">
      <header className="rounded-xl border border-shell-border bg-shell px-5 py-5">
        <h1 className="text-2xl font-semibold tracking-tight text-foreground">
          {title}
        </h1>
        <p className="mt-2 max-w-3xl text-sm leading-7 text-foreground/70">
          Track the app-owned request budget around hotel and travel providers
          without leaving Wandrix. Xotelo is the active hotel search path today,
          while the other RapidAPI providers are already wired into the same
          usage surface for later expansion.
        </p>
      </header>

      {isLoading ? (
        <SurfaceMessage message="Loading provider usage..." />
      ) : error ? (
        <SurfaceMessage message={error} />
      ) : (
        <div className="grid gap-4">
          {statusItems.map((status) => {
            const usage = usageByProvider.get(status.provider);
            return (
              <article
                key={status.provider}
                className="rounded-xl border border-shell-border bg-shell px-5 py-5"
              >
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div>
                    <h2 className="text-base font-semibold text-foreground">
                      {usage?.label ?? formatProviderName(status.provider)}
                    </h2>
                    <p className="mt-1 text-sm leading-7 text-foreground/68">
                      {usage?.message ?? status.message}
                    </p>
                  </div>
                  <span className="rounded-md border border-shell-border bg-panel px-3 py-1.5 text-xs text-foreground/62">
                    {status.status.replaceAll("_", " ")}
                  </span>
                </div>

                <dl className="mt-5 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
                  <Metric label="Monthly quota" value={formatQuota(usage)} />
                  <Metric
                    label="Requests used"
                    value={String(usage?.request_count ?? 0)}
                  />
                  <Metric
                    label="Remaining"
                    value={
                      usage?.remaining_count !== null &&
                      usage?.remaining_count !== undefined
                        ? String(usage.remaining_count)
                        : "Unlimited"
                    }
                  />
                  <Metric
                    label="Success / errors"
                    value={`${usage?.success_count ?? 0} / ${usage?.error_count ?? 0}`}
                  />
                </dl>

                <div className="mt-5 flex flex-wrap gap-2 text-xs text-foreground/58">
                  <span className="rounded-md border border-shell-border bg-panel px-3 py-1.5">
                    Checked {formatTimestamp(status.checked_at)}
                  </span>
                  {usage?.last_used_at ? (
                    <span className="rounded-md border border-shell-border bg-panel px-3 py-1.5">
                      Last request {formatTimestamp(usage.last_used_at)}
                    </span>
                  ) : null}
                  {usage?.last_status ? (
                    <span className="rounded-md border border-shell-border bg-panel px-3 py-1.5">
                      Last response {usage.last_status}
                    </span>
                  ) : null}
                </div>
              </article>
            );
          })}
        </div>
      )}
    </section>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg border border-shell-border bg-panel px-4 py-4">
      <dt className="text-xs font-medium text-foreground/54">{label}</dt>
      <dd className="mt-2 text-sm font-medium text-foreground">{value}</dd>
    </div>
  );
}

function SurfaceMessage({ message }: { message: string }) {
  return (
    <section className="rounded-xl border border-shell-border bg-shell px-5 py-5 text-sm text-foreground/70">
      {message}
    </section>
  );
}

function formatProviderName(provider: string) {
  return provider
    .split("_")
    .map((part) => part[0]?.toUpperCase() + part.slice(1))
    .join(" ");
}

function formatQuota(item: ProviderUsageItem | undefined) {
  if (!item) {
    return "Not tracked yet";
  }

  return item.quota_limit ? `${item.quota_limit} / month` : "Unlimited";
}

function formatTimestamp(value: string) {
  const timestamp = new Date(value);
  if (Number.isNaN(timestamp.getTime())) {
    return value;
  }

  return timestamp.toLocaleString(undefined, {
    day: "numeric",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
  });
}
