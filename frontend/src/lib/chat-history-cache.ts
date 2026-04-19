import type { CheckpointConversationMessage } from "@/types/trip-conversation";

export type PersistedThreadMessage = {
  id?: string;
  role: "assistant" | "user" | "system";
  createdAt?: string;
  content: string;
};

const CHAT_HISTORY_STORAGE_PREFIX = "wandrix:chat-history:";

export function readCachedThreadMessages(tripId: string) {
  const rawValue = window.localStorage.getItem(
    `${CHAT_HISTORY_STORAGE_PREFIX}${tripId}`,
  );

  if (!rawValue) {
    return [] satisfies PersistedThreadMessage[];
  }

  try {
    const parsed = JSON.parse(rawValue);

    if (!Array.isArray(parsed)) {
      return [] satisfies PersistedThreadMessage[];
    }

    return parsed.flatMap((entry) => {
      if (
        !entry ||
        typeof entry !== "object" ||
        !("role" in entry) ||
        !("content" in entry)
      ) {
        return [];
      }

      const candidate = entry as Record<string, unknown>;
      const role = candidate.role;
      const content = candidate.content;

      if (
        (role !== "assistant" && role !== "user" && role !== "system") ||
        typeof content !== "string"
      ) {
        return [];
      }

      return [
        {
          id: typeof candidate.id === "string" ? candidate.id : undefined,
          role,
          content,
          createdAt:
            typeof candidate.createdAt === "string"
              ? candidate.createdAt
              : undefined,
        } satisfies PersistedThreadMessage,
      ];
    });
  } catch {
    return [] satisfies PersistedThreadMessage[];
  }
}

export function writeCachedThreadMessages(
  tripId: string,
  messages: PersistedThreadMessage[],
) {
  window.localStorage.setItem(
    `${CHAT_HISTORY_STORAGE_PREFIX}${tripId}`,
    JSON.stringify(messages),
  );
}

export function normalizeHistoryMessages(
  messages: CheckpointConversationMessage[],
) {
  return messages.map((message, index) => ({
    id: `${message.role}-${index}`,
    role: message.role,
    content: message.content,
    createdAt: message.created_at ?? undefined,
  })) satisfies PersistedThreadMessage[];
}
