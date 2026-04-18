export type BrowserSessionCreateRequest = {
  timezone?: string;
  locale?: string;
};

export type BrowserSessionCreateResponse = {
  browser_session_id: string;
  user_id: string | null;
  timezone: string | null;
  locale: string | null;
  status: "active";
  created_at: string;
};
