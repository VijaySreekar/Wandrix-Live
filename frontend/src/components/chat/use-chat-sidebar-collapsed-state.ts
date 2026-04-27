"use client";

import { useSyncExternalStore, type Dispatch, type SetStateAction } from "react";

const CHAT_SIDEBAR_COLLAPSED_KEY = "wandrix.chat_sidebar_collapsed";
const CHAT_SIDEBAR_COLLAPSED_EVENT = "wandrix:chat-sidebar-collapsed";

function getSnapshot() {
  if (typeof window === "undefined") {
    return false;
  }

  try {
    return window.localStorage.getItem(CHAT_SIDEBAR_COLLAPSED_KEY) === "true";
  } catch {
    return false;
  }
}

function subscribe(onStoreChange: () => void) {
  if (typeof window === "undefined") {
    return () => {};
  }

  const handleStorage = (event: StorageEvent) => {
    if (event.key === CHAT_SIDEBAR_COLLAPSED_KEY) {
      onStoreChange();
    }
  };

  window.addEventListener("storage", handleStorage);
  window.addEventListener(CHAT_SIDEBAR_COLLAPSED_EVENT, onStoreChange);

  return () => {
    window.removeEventListener("storage", handleStorage);
    window.removeEventListener(CHAT_SIDEBAR_COLLAPSED_EVENT, onStoreChange);
  };
}

export function useChatSidebarCollapsedState() {
  const isSidebarCollapsed = useSyncExternalStore(
    subscribe,
    getSnapshot,
    () => false,
  );

  const setIsSidebarCollapsed: Dispatch<SetStateAction<boolean>> = (value) => {
    const nextValue =
      typeof value === "function"
        ? (value as (current: boolean) => boolean)(getSnapshot())
        : value;

    try {
      window.localStorage.setItem(
        CHAT_SIDEBAR_COLLAPSED_KEY,
        nextValue ? "true" : "false",
      );
    } catch {}

    window.dispatchEvent(new Event(CHAT_SIDEBAR_COLLAPSED_EVENT));
  };

  return {
    isSidebarCollapsed,
    setIsSidebarCollapsed,
  };
}
