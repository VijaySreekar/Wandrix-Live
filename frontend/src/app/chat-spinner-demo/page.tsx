"use client";

import { Bot, Sparkles, MessageSquare, Zap, Brain, Wand2 } from "lucide-react";

export default function ChatSpinnerDemoPage() {
  return (
    <div className="min-h-screen bg-background p-8">
      <div className="mx-auto max-w-7xl">
        <h1 className="mb-4 text-3xl font-semibold text-foreground">
          Agent Chat Animations
        </h1>
        <p className="mb-12 max-w-2xl text-sm leading-7 text-foreground/60">
          30 loading animations designed for AI chat interfaces. These work for agent thinking, 
          message sending, and response generation states. Click any to copy its number.
        </p>
        
        <div className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-3">
          {chatSpinners.map((spinner, index) => (
            <div
              key={index}
              className="flex flex-col gap-4 rounded-xl border border-border bg-card p-6 transition-all hover:border-[color:var(--accent)] hover:shadow-lg cursor-pointer"
              onClick={() => {
                navigator.clipboard.writeText(`#${index + 1}`);
                alert(`Copied: Chat Spinner #${index + 1}`);
              }}
            >
              <div className="flex min-h-[100px] items-center justify-center">
                {spinner.component()}
              </div>
              <div className="space-y-1 border-t border-border pt-4">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-medium text-foreground/50">
                    #{index + 1}
                  </span>
                  <span className="text-xs text-foreground/40">
                    {spinner.type}
                  </span>
                </div>
                <p className="text-sm font-medium text-foreground">
                  {spinner.name}
                </p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

// 30 Chat-Specific Loading Animations
const chatSpinners = [
  // 1. Typing dots (classic)
  {
    name: "Typing Dots",
    type: "thinking",
    component: () => (
      <div className="flex items-center gap-1.5">
        <div className="h-2.5 w-2.5 animate-bounce rounded-full bg-[color:var(--accent)] [animation-delay:-0.3s]" />
        <div className="h-2.5 w-2.5 animate-bounce rounded-full bg-[color:var(--accent)] [animation-delay:-0.15s]" />
        <div className="h-2.5 w-2.5 animate-bounce rounded-full bg-[color:var(--accent)]" />
      </div>
    ),
  },

  // 2. AI brain pulse
  {
    name: "AI Brain Pulse",
    type: "thinking",
    component: () => (
      <div className="relative">
        <div className="absolute inset-0 animate-ping rounded-full bg-[color:var(--accent)]/20" />
        <Brain className="h-8 w-8 animate-pulse text-[color:var(--accent)]" />
      </div>
    ),
  },

  // 3. Sparkle burst
  {
    name: "Sparkle Burst",
    type: "generating",
    component: () => (
      <div className="relative h-10 w-10">
        {[0, 1, 2, 3].map((i) => (
          <div
            key={i}
            className="absolute inset-0 animate-ping"
            style={{ animationDelay: `${i * 0.2}s` }}
          >
            <Sparkles className="h-10 w-10 text-[color:var(--accent)]" style={{ opacity: 0.3 }} />
          </div>
        ))}
        <Sparkles className="h-10 w-10 text-[color:var(--accent)]" />
      </div>
    ),
  },

  // 4. Bot thinking
  {
    name: "Bot Thinking",
    type: "thinking",
    component: () => (
      <div className="flex items-center gap-3">
        <Bot className="h-6 w-6 text-[color:var(--accent)]" />
        <div className="flex gap-1">
          <div className="h-1.5 w-1.5 animate-pulse rounded-full bg-[color:var(--accent)] [animation-delay:-0.3s]" />
          <div className="h-1.5 w-1.5 animate-pulse rounded-full bg-[color:var(--accent)] [animation-delay:-0.15s]" />
          <div className="h-1.5 w-1.5 animate-pulse rounded-full bg-[color:var(--accent)]" />
        </div>
      </div>
    ),
  },

  // 5. Message wave
  {
    name: "Message Wave",
    type: "sending",
    component: () => (
      <div className="flex items-center gap-1">
        {[0, 1, 2, 3, 4].map((i) => (
          <div
            key={i}
            className="w-1 rounded-full bg-[color:var(--accent)]"
            style={{
              height: '8px',
              animation: 'wave 1s ease-in-out infinite',
              animationDelay: `${i * 0.1}s`,
            }}
          />
        ))}
        <style jsx>{`
          @keyframes wave {
            0%, 100% { height: 8px; }
            50% { height: 20px; }
          }
        `}</style>
      </div>
    ),
  },

  // 6. Wand magic
  {
    name: "Wand Magic",
    type: "generating",
    component: () => (
      <div className="relative">
        <Wand2 className="h-8 w-8 animate-pulse text-[color:var(--accent)]" />
        <div className="absolute -right-1 -top-1 h-2 w-2 animate-ping rounded-full bg-[color:var(--accent)]" />
      </div>
    ),
  },

  // 7. Pulse ring
  {
    name: "Pulse Ring",
    type: "thinking",
    component: () => (
      <div className="relative h-12 w-12">
        <div className="absolute inset-0 animate-ping rounded-full border-2 border-[color:var(--accent)]" />
        <div className="absolute inset-0 flex items-center justify-center">
          <div className="h-3 w-3 rounded-full bg-[color:var(--accent)]" />
        </div>
      </div>
    ),
  },

  // 8. Typing indicator
  {
    name: "Typing Indicator",
    type: "typing",
    component: () => (
      <div className="flex items-center gap-2 rounded-full bg-[color:var(--accent)]/10 px-4 py-2">
        <div className="flex gap-1">
          <div className="h-2 w-2 animate-bounce rounded-full bg-[color:var(--accent)] [animation-delay:-0.3s]" />
          <div className="h-2 w-2 animate-bounce rounded-full bg-[color:var(--accent)] [animation-delay:-0.15s]" />
          <div className="h-2 w-2 animate-bounce rounded-full bg-[color:var(--accent)]" />
        </div>
      </div>
    ),
  },

  // 9. Zap energy
  {
    name: "Zap Energy",
    type: "generating",
    component: () => (
      <div className="relative">
        <Zap className="h-8 w-8 animate-pulse text-[color:var(--accent)]" />
        <div className="absolute inset-0 animate-ping">
          <Zap className="h-8 w-8 text-[color:var(--accent)]/30" />
        </div>
      </div>
    ),
  },

  // 10. Dots expanding
  {
    name: "Dots Expanding",
    type: "thinking",
    component: () => (
      <div className="flex items-center gap-2">
        {[0, 1, 2].map((i) => (
          <div
            key={i}
            className="animate-ping rounded-full bg-[color:var(--accent)]"
            style={{
              width: `${8 + i * 2}px`,
              height: `${8 + i * 2}px`,
              animationDelay: `${i * 0.2}s`,
            }}
          />
        ))}
      </div>
    ),
  },

  // 11. Gradient wave
  {
    name: "Gradient Wave",
    type: "generating",
    component: () => (
      <div className="relative h-1 w-24 overflow-hidden rounded-full bg-[color:var(--accent)]/20">
        <div className="absolute inset-y-0 w-1/2 animate-[slide_1.5s_ease-in-out_infinite] rounded-full bg-gradient-to-r from-transparent via-[color:var(--accent)] to-transparent" />
        <style jsx>{`
          @keyframes slide {
            0% { left: -50%; }
            100% { left: 100%; }
          }
        `}</style>
      </div>
    ),
  },

  // 12. Circular dots
  {
    name: "Circular Dots",
    type: "thinking",
    component: () => (
      <div className="relative h-12 w-12">
        {[0, 1, 2, 3, 4, 5].map((i) => (
          <div
            key={i}
            className="absolute left-1/2 top-0 h-2 w-2 -translate-x-1/2 animate-pulse rounded-full bg-[color:var(--accent)]"
            style={{
              transform: `rotate(${i * 60}deg) translateY(20px)`,
              animationDelay: `${i * 0.15}s`,
            }}
          />
        ))}
      </div>
    ),
  },

  // 13. Message bubble
  {
    name: "Message Bubble",
    type: "typing",
    component: () => (
      <div className="flex items-center gap-2 rounded-2xl border border-[color:var(--accent)]/30 bg-[color:var(--accent)]/5 px-4 py-3">
        <MessageSquare className="h-4 w-4 text-[color:var(--accent)]" />
        <div className="flex gap-1">
          <div className="h-1.5 w-1.5 animate-bounce rounded-full bg-[color:var(--accent)] [animation-delay:-0.3s]" />
          <div className="h-1.5 w-1.5 animate-bounce rounded-full bg-[color:var(--accent)] [animation-delay:-0.15s]" />
          <div className="h-1.5 w-1.5 animate-bounce rounded-full bg-[color:var(--accent)]" />
        </div>
      </div>
    ),
  },

  // 14. Spin fade
  {
    name: "Spin Fade",
    type: "thinking",
    component: () => (
      <div className="relative h-10 w-10">
        <div className="absolute inset-0 animate-spin">
          <div className="h-full w-full rounded-full bg-gradient-to-tr from-[color:var(--accent)] to-transparent" />
          <div className="absolute inset-1 rounded-full bg-background" />
        </div>
      </div>
    ),
  },

  // 15. Bouncing bot
  {
    name: "Bouncing Bot",
    type: "thinking",
    component: () => (
      <Bot className="h-8 w-8 animate-bounce text-[color:var(--accent)]" />
    ),
  },

  // 16. Ripple effect
  {
    name: "Ripple Effect",
    type: "generating",
    component: () => (
      <div className="relative h-14 w-14">
        {[0, 1, 2].map((i) => (
          <div
            key={i}
            className="absolute inset-0 animate-ping rounded-full border-2 border-[color:var(--accent)]"
            style={{
              animationDelay: `${i * 0.4}s`,
              animationDuration: '1.5s',
            }}
          />
        ))}
      </div>
    ),
  },

  // 17. Horizontal bars
  {
    name: "Horizontal Bars",
    type: "sending",
    component: () => (
      <div className="flex flex-col gap-1.5">
        {[0, 1, 2].map((i) => (
          <div
            key={i}
            className="h-1 w-16 animate-pulse rounded-full bg-[color:var(--accent)]"
            style={{ animationDelay: `${i * 0.2}s` }}
          />
        ))}
      </div>
    ),
  },

  // 18. Sparkle rotate
  {
    name: "Sparkle Rotate",
    type: "generating",
    component: () => (
      <div className="animate-spin" style={{ animationDuration: '2s' }}>
        <Sparkles className="h-8 w-8 text-[color:var(--accent)]" />
      </div>
    ),
  },

  // 19. Double ring
  {
    name: "Double Ring",
    type: "thinking",
    component: () => (
      <div className="relative h-12 w-12">
        <div className="absolute inset-0 animate-spin">
          <div className="h-full w-full rounded-full border-2 border-transparent border-t-[color:var(--accent)]" />
        </div>
        <div className="absolute inset-2 animate-spin" style={{ animationDirection: 'reverse' }}>
          <div className="h-full w-full rounded-full border-2 border-transparent border-t-[color:var(--accent)]/50" />
        </div>
      </div>
    ),
  },

  // 20. Pulse scale
  {
    name: "Pulse Scale",
    type: "thinking",
    component: () => (
      <div className="h-8 w-8 animate-pulse rounded-full bg-[color:var(--accent)]" />
    ),
  },

  // 21. Dots trail
  {
    name: "Dots Trail",
    type: "sending",
    component: () => (
      <div className="flex items-center gap-1">
        {[0, 1, 2, 3, 4, 5].map((i) => (
          <div
            key={i}
            className="h-2 w-2 animate-pulse rounded-full bg-[color:var(--accent)]"
            style={{
              opacity: 0.3 + (i / 5) * 0.7,
              animationDelay: `${i * 0.1}s`,
            }}
          />
        ))}
      </div>
    ),
  },

  // 22. Brain wave
  {
    name: "Brain Wave",
    type: "thinking",
    component: () => (
      <div className="flex items-center gap-2">
        <Brain className="h-6 w-6 text-[color:var(--accent)]" />
        <div className="flex items-center gap-0.5">
          {[0, 1, 2, 3, 4].map((i) => (
            <div
              key={i}
              className="w-0.5 rounded-full bg-[color:var(--accent)]"
              style={{
                height: '6px',
                animation: 'wave 1s ease-in-out infinite',
                animationDelay: `${i * 0.1}s`,
              }}
            />
          ))}
        </div>
        <style jsx>{`
          @keyframes wave {
            0%, 100% { height: 6px; }
            50% { height: 16px; }
          }
        `}</style>
      </div>
    ),
  },

  // 23. Orbit dot
  {
    name: "Orbit Dot",
    type: "thinking",
    component: () => (
      <div className="relative h-12 w-12">
        <div className="absolute inset-0 rounded-full border border-dashed border-[color:var(--accent)]/30" />
        <div className="absolute inset-0 animate-spin" style={{ animationDuration: '2s' }}>
          <div className="h-2.5 w-2.5 rounded-full bg-[color:var(--accent)]" />
        </div>
      </div>
    ),
  },

  // 24. Fade in out
  {
    name: "Fade In Out",
    type: "thinking",
    component: () => (
      <div className="flex gap-2">
        {[0, 1, 2].map((i) => (
          <div
            key={i}
            className="h-3 w-3 animate-pulse rounded-full bg-[color:var(--accent)]"
            style={{ animationDelay: `${i * 0.3}s` }}
          />
        ))}
      </div>
    ),
  },

  // 25. Loading bar
  {
    name: "Loading Bar",
    type: "sending",
    component: () => (
      <div className="relative h-1.5 w-24 overflow-hidden rounded-full bg-[color:var(--accent)]/20">
        <div className="absolute inset-y-0 left-0 w-1/3 animate-[travel_1.5s_ease-in-out_infinite] rounded-full bg-[color:var(--accent)]" />
        <style jsx>{`
          @keyframes travel {
            0% { left: -33.33%; }
            100% { left: 100%; }
          }
        `}</style>
      </div>
    ),
  },

  // 26. Concentric pulse
  {
    name: "Concentric Pulse",
    type: "thinking",
    component: () => (
      <div className="relative h-12 w-12">
        {[0, 1, 2].map((i) => (
          <div
            key={i}
            className="absolute rounded-full border-2 border-[color:var(--accent)]"
            style={{
              inset: `${i * 4}px`,
              animation: 'pulse 2s ease-in-out infinite',
              animationDelay: `${i * 0.2}s`,
            }}
          />
        ))}
      </div>
    ),
  },

  // 27. Sparkle pulse
  {
    name: "Sparkle Pulse",
    type: "generating",
    component: () => (
      <div className="relative h-10 w-10">
        <div className="absolute inset-0 animate-ping">
          <Sparkles className="h-10 w-10 text-[color:var(--accent)]/30" />
        </div>
        <Sparkles className="h-10 w-10 animate-pulse text-[color:var(--accent)]" />
      </div>
    ),
  },

  // 28. Typing wave
  {
    name: "Typing Wave",
    type: "typing",
    component: () => (
      <div className="flex items-end gap-1">
        {[0, 1, 2, 3].map((i) => (
          <div
            key={i}
            className="w-1.5 animate-bounce rounded-full bg-[color:var(--accent)]"
            style={{
              height: `${8 + (i % 2) * 4}px`,
              animationDelay: `${i * 0.15}s`,
            }}
          />
        ))}
      </div>
    ),
  },

  // 29. Glow pulse
  {
    name: "Glow Pulse",
    type: "generating",
    component: () => (
      <div className="relative">
        <div className="absolute inset-0 animate-ping rounded-full bg-[color:var(--accent)]/40 blur-md" />
        <div className="relative h-6 w-6 rounded-full bg-[color:var(--accent)]" />
      </div>
    ),
  },

  // 30. Staggered dots
  {
    name: "Staggered Dots",
    type: "thinking",
    component: () => (
      <div className="flex items-center gap-1.5">
        {[0, 1, 2, 3, 4].map((i) => (
          <div
            key={i}
            className="rounded-full bg-[color:var(--accent)]"
            style={{
              width: `${6 + (i % 3) * 2}px`,
              height: `${6 + (i % 3) * 2}px`,
              animation: 'pulse 1.5s ease-in-out infinite',
              animationDelay: `${i * 0.15}s`,
            }}
          />
        ))}
      </div>
    ),
  },
];
