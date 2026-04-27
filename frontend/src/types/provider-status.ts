export type ProviderHealthStatus = "ok" | "error" | "not_configured";

export type ProviderStatusItem = {
  provider: string;
  status: ProviderHealthStatus;
  message: string;
  checked_at: string;
};

export type ProviderStatusResponse = {
  items: ProviderStatusItem[];
};
