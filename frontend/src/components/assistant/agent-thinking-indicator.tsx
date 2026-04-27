"use client";

/**
 * Conversational thinking indicators for the AI agent
 * These appear in the chat when the agent is processing a response
 */

export function AgentThinkingDots() {
  return (
    <div className="flex items-center gap-1.5">
      <div className="h-2 w-2 animate-bounce rounded-full bg-[color:var(--accent)] [animation-delay:-0.3s]" />
      <div className="h-2 w-2 animate-bounce rounded-full bg-[color:var(--accent)] [animation-delay:-0.15s]" />
      <div className="h-2 w-2 animate-bounce rounded-full bg-[color:var(--accent)]" />
    </div>
  );
}

export function AgentThinkingWave() {
  return (
    <div className="flex items-center gap-1">
      {[0, 1, 2, 3, 4].map((i) => (
        <div
          key={i}
          className="w-0.5 rounded-full bg-[color:var(--accent)]"
          style={{
            height: '6px',
            animation: 'wave 1.2s ease-in-out infinite',
            animationDelay: `${i * 0.1}s`,
          }}
        />
      ))}
      <style jsx>{`
        @keyframes wave {
          0%, 100% { height: 6px; opacity: 0.4; }
          50% { height: 16px; opacity: 1; }
        }
      `}</style>
    </div>
  );
}

export function AgentThinkingPulse() {
  return (
    <div className="flex items-center gap-1.5">
      {[0, 1, 2].map((i) => (
        <div
          key={i}
          className="animate-pulse rounded-full bg-[color:var(--accent)]"
          style={{
            width: `${6 + i * 2}px`,
            height: `${6 + i * 2}px`,
            animationDelay: `${i * 0.2}s`,
          }}
        />
      ))}
    </div>
  );
}

export function AgentThinkingTyping() {
  return (
    <div className="inline-flex items-center gap-2 rounded-full bg-[color:var(--accent)]/8 px-3 py-1.5">
      <div className="flex gap-1">
        <div className="h-1.5 w-1.5 animate-bounce rounded-full bg-[color:var(--accent)] [animation-delay:-0.3s]" />
        <div className="h-1.5 w-1.5 animate-bounce rounded-full bg-[color:var(--accent)] [animation-delay:-0.15s]" />
        <div className="h-1.5 w-1.5 animate-bounce rounded-full bg-[color:var(--accent)]" />
      </div>
    </div>
  );
}

export function AgentThinkingEllipsis() {
  return (
    <div className="flex items-center gap-1">
      {[0, 1, 2, 3, 4, 5].map((i) => (
        <div
          key={i}
          className="h-1.5 w-1.5 animate-pulse rounded-full bg-[color:var(--accent)]"
          style={{
            opacity: 0.3 + (i / 5) * 0.7,
            animationDelay: `${i * 0.1}s`,
          }}
        />
      ))}
    </div>
  );
}

export function AgentThinkingBubble() {
  return (
    <div className="relative inline-flex items-center gap-2 rounded-2xl border border-[color:var(--accent)]/20 bg-[color:var(--accent)]/5 px-4 py-2.5">
      <div className="flex gap-1.5">
        <div className="h-2 w-2 animate-bounce rounded-full bg-[color:var(--accent)] [animation-delay:-0.3s]" />
        <div className="h-2 w-2 animate-bounce rounded-full bg-[color:var(--accent)] [animation-delay:-0.15s]" />
        <div className="h-2 w-2 animate-bounce rounded-full bg-[color:var(--accent)]" />
      </div>
    </div>
  );
}

export function AgentThinkingRipple() {
  return (
    <div className="relative flex h-8 w-8 items-center justify-center">
      <div className="absolute inset-0 animate-ping rounded-full bg-[color:var(--accent)]/20" />
      <div className="absolute inset-1 animate-ping rounded-full bg-[color:var(--accent)]/30" style={{ animationDelay: '0.3s' }} />
      <div className="h-2 w-2 rounded-full bg-[color:var(--accent)]" />
    </div>
  );
}

export function AgentThinkingMinimal() {
  return (
    <div className="flex items-center gap-1">
      <div className="h-1 w-1 animate-pulse rounded-full bg-[color:var(--accent)] [animation-delay:-0.3s]" />
      <div className="h-1 w-1 animate-pulse rounded-full bg-[color:var(--accent)] [animation-delay:-0.15s]" />
      <div className="h-1 w-1 animate-pulse rounded-full bg-[color:var(--accent)]" />
    </div>
  );
}

// Default export - the recommended thinking indicator
export default AgentThinkingDots;
