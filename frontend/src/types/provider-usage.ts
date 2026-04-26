export type ProviderUsageItem = {
  provider: string;
  label: string;
  quota_limit: number | null;
  request_count: number;
  success_count: number;
  error_count: number;
  remaining_count: number | null;
  usage_month: string;
  last_status: string | null;
  last_used_at: string | null;
  message: string;
};

export type ProviderUsageResponse = {
  items: ProviderUsageItem[];
};
