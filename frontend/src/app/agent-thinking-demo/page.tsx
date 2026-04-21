"use client";

import { Bot } from "lucide-react";

export default function AgentThinkingDemoPage() {
  return (
    <div className="min-h-screen bg-background p-8">
      <div className="mx-auto max-w-5xl">
        <h1 className="mb-4 text-3xl font-semibold text-foreground">
          Agent Thinking Animations
        </h1>
        <p className="mb-12 max-w-2xl text-sm leading-7 text-foreground/60">
          15 conversational thinking indicators for when the AI agent is processing a response.
          These appear in the chat interface to show the agent is working. Click any to copy its number.
        </p>
        
        <div className="space-y-6">
          {thinkingAnimations.map((animation, index) => (
            <div
              key={index}
              className="group cursor-pointer rounded-xl border border-border bg-card p-6 transition-all hover:border-[color:var(--accent)] hover:shadow-lg"
              onClick={() => {
                navigator.clipboard.writeText(`#${index + 1}: ${animation.name}`);
                alert(`Copied: #${index + 1} - ${animation.name}`);
              }}
            >
              <div className="mb-4 flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <span className="text-xs font-medium text-foreground/50">
                    #{index + 1}
                  </span>
                  <h3 className="text-sm font-semibold text-foreground">
                    {animation.name}
                  </h3>
                </div>
                <span className="text-xs text-foreground/40">
                  {animation.style}
                </span>
              </div>
              
              {/* Chat message preview */}
              <div className="rounded-lg border border-border/50 bg-background/50 p-4">
                <div className="flex items-center gap-3">
                  <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-[color:color-mix(in_srgb,var(--accent)_12%,transparent)] text-[color:var(--accent)] shadow-sm ring-1 ring-[color:color-mix(in_srgb,var(--accent)_14%,transparent)]">
                    <Bot className="h-4 w-4" />
                  </div>
                  <div className="flex min-h-[60px] flex-1 items-center">
                    {animation.component()}
                  </div>
                </div>
              </div>
              
              <p className="mt-3 text-xs leading-relaxed text-foreground/50">
                {animation.description}
              </p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

const thinkingAnimations = [
  // 1. Classic bouncing dots
  {
    name: "Bouncing Dots",
    style: "classic",
    description: "The most recognizable chat typing indicator. Three dots bouncing in sequence.",
    component: () => (
      <div className="flex items-center gap-1.5">
        <div className="h-2.5 w-2.5 animate-bounce rounded-full bg-[color:var(--accent)] [animation-delay:-0.3s]" />
        <div className="h-2.5 w-2.5 animate-bounce rounded-full bg-[color:var(--accent)] [animation-delay:-0.15s]" />
        <div className="h-2.5 w-2.5 animate-bounce rounded-full bg-[color:var(--accent)]" />
      </div>
    ),
  },

  // 2. Wave bars
  {
    name: "Wave Bars",
    style: "modern",
    description: "Audio visualizer style with bars that wave up and down, suggesting active processing.",
    component: () => (
      <div className="flex items-center gap-1">
        {[0, 1, 2, 3, 4].map((i) => (
          <div
            key={i}
            className="w-1 rounded-full bg-[color:var(--accent)]"
            style={{
              height: '8px',
              animation: 'wave 1.2s ease-in-out infinite',
              animationDelay: `${i * 0.1}s`,
            }}
          />
        ))}
        <style jsx>{`
          @keyframes wave {
            0%, 100% { height: 8px; opacity: 0.5; }
            50% { height: 20px; opacity: 1; }
          }
        `}</style>
      </div>
    ),
  },

  // 3. Pulsing dots
  {
    name: "Pulsing Dots",
    style: "smooth",
    description: "Gentle pulsing effect with growing dots, feels calm and thoughtful.",
    component: () => (
      <div className="flex items-center gap-2">
        {[0, 1, 2].map((i) => (
          <div
            key={i}
            className="animate-pulse rounded-full bg-[color:var(--accent)]"
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

  // 4. Typing bubble
  {
    name: "Typing Bubble",
    style: "conversational",
    description: "Dots inside a chat bubble background, mimics iMessage typing indicator.",
    component: () => (
      <div className="inline-flex items-center gap-2 rounded-full bg-[color:var(--accent)]/10 px-4 py-2">
        <div className="flex gap-1.5">
          <div className="h-2 w-2 animate-bounce rounded-full bg-[color:var(--accent)] [animation-delay:-0.3s]" />
          <div className="h-2 w-2 animate-bounce rounded-full bg-[color:var(--accent)] [animation-delay:-0.15s]" />
          <div className="h-2 w-2 animate-bounce rounded-full bg-[color:var(--accent)]" />
        </div>
      </div>
    ),
  },

  // 5. Ellipsis trail
  {
    name: "Ellipsis Trail",
    style: "minimal",
    description: "Fading dots creating a trailing effect, subtle and elegant.",
    component: () => (
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
    ),
  },

  // 6. Ripple effect
  {
    name: "Ripple Effect",
    style: "dynamic",
    description: "Expanding ripples from a center point, suggests radiating thought.",
    component: () => (
      <div className="relative flex h-10 w-10 items-center justify-center">
        <div className="absolute inset-0 animate-ping rounded-full bg-[color:var(--accent)]/20" />
        <div className="absolute inset-1 animate-ping rounded-full bg-[color:var(--accent)]/30" style={{ animationDelay: '0.3s' }} />
        <div className="h-2.5 w-2.5 rounded-full bg-[color:var(--accent)]" />
      </div>
    ),
  },

  // 7. Chat bubble with dots
  {
    name: "Chat Bubble",
    style: "conversational",
    description: "Full chat bubble styling with border and background, very messaging-app like.",
    component: () => (
      <div className="inline-flex items-center gap-2 rounded-2xl border border-[color:var(--accent)]/20 bg-[color:var(--accent)]/5 px-4 py-2.5">
        <div className="flex gap-1.5">
          <div className="h-2 w-2 animate-bounce rounded-full bg-[color:var(--accent)] [animation-delay:-0.3s]" />
          <div className="h-2 w-2 animate-bounce rounded-full bg-[color:var(--accent)] [animation-delay:-0.15s]" />
          <div className="h-2 w-2 animate-bounce rounded-full bg-[color:var(--accent)]" />
        </div>
      </div>
    ),
  },

  // 8. Minimal dots
  {
    name: "Minimal Dots",
    style: "subtle",
    description: "Tiny pulsing dots, very understated and clean.",
    component: () => (
      <div className="flex items-center gap-1.5">
        <div className="h-1 w-1 animate-pulse rounded-full bg-[color:var(--accent)] [animation-delay:-0.3s]" />
        <div className="h-1 w-1 animate-pulse rounded-full bg-[color:var(--accent)] [animation-delay:-0.15s]" />
        <div className="h-1 w-1 animate-pulse rounded-full bg-[color:var(--accent)]" />
      </div>
    ),
  },

  // 9. Staggered pulse
  {
    name: "Staggered Pulse",
    style: "rhythmic",
    description: "Five dots with varying sizes pulsing in sequence, creates rhythm.",
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

  // 10. Breathing circle
  {
    name: "Breathing Circle",
    style: "calm",
    description: "Single circle that breathes in and out, meditative feel.",
    component: () => (
      <div className="h-3 w-3 animate-pulse rounded-full bg-[color:var(--accent)]" style={{ animationDuration: '2s' }} />
    ),
  },

  // 11. Double wave
  {
    name: "Double Wave",
    style: "energetic",
    description: "Two sets of wave bars for a more active, energetic feel.",
    component: () => (
      <div className="flex items-center gap-3">
        <div className="flex items-center gap-0.5">
          {[0, 1, 2].map((i) => (
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
        <div className="flex items-center gap-0.5">
          {[0, 1, 2].map((i) => (
            <div
              key={i}
              className="w-0.5 rounded-full bg-[color:var(--accent)]"
              style={{
                height: '6px',
                animation: 'wave 1s ease-in-out infinite',
                animationDelay: `${i * 0.1 + 0.15}s`,
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

  // 12. Fade sequence
  {
    name: "Fade Sequence",
    style: "smooth",
    description: "Three dots fading in and out in sequence, smooth transitions.",
    component: () => (
      <div className="flex gap-2">
        {[0, 1, 2].map((i) => (
          <div
            key={i}
            className="h-2.5 w-2.5 animate-pulse rounded-full bg-[color:var(--accent)]"
            style={{ animationDelay: `${i * 0.3}s`, animationDuration: '1.5s' }}
          />
        ))}
      </div>
    ),
  },

  // 13. Orbit dot
  {
    name: "Orbit Dot",
    style: "dynamic",
    description: "Dot orbiting around a center point, suggests circular thinking.",
    component: () => (
      <div className="relative h-10 w-10">
        <div className="absolute inset-0 rounded-full border border-dashed border-[color:var(--accent)]/20" />
        <div className="absolute inset-0 animate-spin" style={{ animationDuration: '2s' }}>
          <div className="h-2 w-2 rounded-full bg-[color:var(--accent)]" />
        </div>
      </div>
    ),
  },

  // 14. Typing wave
  {
    name: "Typing Wave",
    style: "playful",
    description: "Bouncing bars with varying heights, playful and friendly.",
    component: () => (
      <div className="flex items-end gap-1">
        {[0, 1, 2, 3].map((i) => (
          <div
            key={i}
            className="w-1.5 animate-bounce rounded-full bg-[color:var(--accent)]"
            style={{
              height: `${10 + (i % 2) * 6}px`,
              animationDelay: `${i * 0.15}s`,
            }}
          />
        ))}
      </div>
    ),
  },

  // 15. Glow pulse
  {
    name: "Glow Pulse",
    style: "premium",
    description: "Pulsing dot with a glowing blur effect, premium feel.",
    component: () => (
      <div className="relative">
        <div className="absolute inset-0 animate-ping rounded-full bg-[color:var(--accent)]/40 blur-sm" />
        <div className="relative h-3 w-3 rounded-full bg-[color:var(--accent)]" />
      </div>
    ),
  },

  // 16. Heartbeat
  {
    name: "Heartbeat",
    style: "organic",
    description: "Pulsing like a heartbeat, suggests the AI is 'alive' and thinking.",
    component: () => (
      <div className="flex items-center gap-2">
        <div className="h-2.5 w-2.5 animate-ping rounded-full bg-[color:var(--accent)]" style={{ animationDuration: '1s' }} />
        <div className="h-2.5 w-2.5 animate-ping rounded-full bg-[color:var(--accent)]" style={{ animationDuration: '1s', animationDelay: '0.5s' }} />
      </div>
    ),
  },

  // 17. Scanning line
  {
    name: "Scanning Line",
    style: "tech",
    description: "Horizontal line scanning back and forth, tech-inspired.",
    component: () => (
      <div className="relative h-1 w-20 overflow-hidden rounded-full bg-[color:var(--accent)]/20">
        <div className="absolute inset-y-0 w-1/3 animate-[scan_2s_ease-in-out_infinite] rounded-full bg-[color:var(--accent)]" />
        <style jsx>{`
          @keyframes scan {
            0%, 100% { left: 0; }
            50% { left: 66.67%; }
          }
        `}</style>
      </div>
    ),
  },

  // 18. Particle burst
  {
    name: "Particle Burst",
    style: "energetic",
    description: "Multiple dots bursting outward, suggests idea generation.",
    component: () => (
      <div className="relative h-12 w-12">
        {[0, 45, 90, 135, 180, 225, 270, 315].map((angle, i) => (
          <div
            key={i}
            className="absolute left-1/2 top-1/2 h-1.5 w-1.5 -translate-x-1/2 -translate-y-1/2 animate-ping rounded-full bg-[color:var(--accent)]"
            style={{
              transform: `rotate(${angle}deg) translateY(-12px)`,
              animationDelay: `${i * 0.1}s`,
            }}
          />
        ))}
      </div>
    ),
  },

  // 19. Morse code
  {
    name: "Morse Code",
    style: "playful",
    description: "Dots and dashes like morse code, playful communication theme.",
    component: () => (
      <div className="flex items-center gap-1">
        <div className="h-2 w-2 animate-pulse rounded-full bg-[color:var(--accent)]" />
        <div className="h-2 w-6 animate-pulse rounded-full bg-[color:var(--accent)]" style={{ animationDelay: '0.2s' }} />
        <div className="h-2 w-2 animate-pulse rounded-full bg-[color:var(--accent)]" style={{ animationDelay: '0.4s' }} />
      </div>
    ),
  },

  // 20. Spinner ring
  {
    name: "Spinner Ring",
    style: "classic",
    description: "Traditional loading spinner, familiar and reliable.",
    component: () => (
      <div className="h-6 w-6 animate-spin rounded-full border-2 border-transparent border-t-[color:var(--accent)]" />
    ),
  },

  // 21. Double spinner
  {
    name: "Double Spinner",
    style: "dynamic",
    description: "Two counter-rotating rings, more complex processing feel.",
    component: () => (
      <div className="relative h-8 w-8">
        <div className="absolute inset-0 animate-spin rounded-full border-2 border-transparent border-t-[color:var(--accent)]" />
        <div className="absolute inset-1 animate-spin rounded-full border-2 border-transparent border-t-[color:var(--accent)]/50" style={{ animationDirection: 'reverse' }} />
      </div>
    ),
  },

  // 22. Bouncing ball
  {
    name: "Bouncing Ball",
    style: "playful",
    description: "Single ball bouncing up and down, friendly and approachable.",
    component: () => (
      <div className="h-3 w-3 animate-bounce rounded-full bg-[color:var(--accent)]" />
    ),
  },

  // 23. Pendulum swing
  {
    name: "Pendulum Swing",
    style: "smooth",
    description: "Dot swinging like a pendulum, rhythmic and hypnotic.",
    component: () => (
      <div className="relative h-8 w-16">
        <div className="absolute left-1/2 top-0 h-full w-0.5 -translate-x-1/2 bg-[color:var(--accent)]/10" />
        <div className="absolute left-1/2 top-0 h-2 w-2 -translate-x-1/2 animate-[swing_2s_ease-in-out_infinite] rounded-full bg-[color:var(--accent)]" />
        <style jsx>{`
          @keyframes swing {
            0%, 100% { transform: translateX(-24px) translateY(24px); }
            50% { transform: translateX(24px) translateY(24px); }
          }
        `}</style>
      </div>
    ),
  },

  // 24. DNA helix
  {
    name: "DNA Helix",
    style: "scientific",
    description: "Dots forming a helix pattern, suggests complex processing.",
    component: () => (
      <div className="flex items-center gap-2">
        {[0, 1, 2, 3, 4].map((i) => (
          <div
            key={i}
            className="h-2 w-2 animate-bounce rounded-full bg-[color:var(--accent)]"
            style={{
              animationDelay: `${i * 0.1}s`,
              opacity: 0.4 + Math.sin(i) * 0.3,
            }}
          />
        ))}
      </div>
    ),
  },

  // 25. Typewriter
  {
    name: "Typewriter",
    style: "vintage",
    description: "Blinking cursor effect, classic writing indicator.",
    component: () => (
      <div className="flex items-center gap-1">
        <div className="h-4 w-0.5 animate-pulse bg-[color:var(--accent)]" style={{ animationDuration: '1s' }} />
      </div>
    ),
  },

  // 26. Radar sweep
  {
    name: "Radar Sweep",
    style: "tech",
    description: "Rotating radar line, suggests scanning and analyzing.",
    component: () => (
      <div className="relative h-10 w-10">
        <div className="absolute inset-0 rounded-full border border-[color:var(--accent)]/20" />
        <div className="absolute inset-0 animate-spin" style={{ animationDuration: '2s' }}>
          <div className="h-full w-1/2 origin-right bg-gradient-to-r from-transparent to-[color:var(--accent)]/30" style={{ borderRadius: '100% 0 0 100%' }} />
        </div>
      </div>
    ),
  },

  // 27. Snowflake
  {
    name: "Snowflake",
    style: "elegant",
    description: "Dots arranged in snowflake pattern, elegant and unique.",
    component: () => (
      <div className="relative h-10 w-10">
        {[0, 60, 120, 180, 240, 300].map((angle, i) => (
          <div
            key={i}
            className="absolute left-1/2 top-1/2 h-1.5 w-1.5 -translate-x-1/2 -translate-y-1/2 animate-pulse rounded-full bg-[color:var(--accent)]"
            style={{
              transform: `rotate(${angle}deg) translateY(-14px)`,
              animationDelay: `${i * 0.1}s`,
            }}
          />
        ))}
      </div>
    ),
  },

  // 28. Equalizer
  {
    name: "Equalizer",
    style: "audio",
    description: "Multiple bars like an audio equalizer, dynamic and modern.",
    component: () => (
      <div className="flex items-end gap-0.5">
        {[0, 1, 2, 3, 4, 5, 6].map((i) => (
          <div
            key={i}
            className="w-1 rounded-full bg-[color:var(--accent)]"
            style={{
              height: '8px',
              animation: 'eq 1s ease-in-out infinite',
              animationDelay: `${i * 0.1}s`,
            }}
          />
        ))}
        <style jsx>{`
          @keyframes eq {
            0%, 100% { height: 8px; }
            50% { height: ${Math.random() * 16 + 8}px; }
          }
        `}</style>
      </div>
    ),
  },

  // 29. Spiral
  {
    name: "Spiral",
    style: "hypnotic",
    description: "Dots in spiral formation, mesmerizing effect.",
    component: () => (
      <div className="relative h-12 w-12">
        {[0, 1, 2, 3, 4, 5, 6, 7].map((i) => (
          <div
            key={i}
            className="absolute left-1/2 top-1/2 h-1.5 w-1.5 -translate-x-1/2 -translate-y-1/2 animate-pulse rounded-full bg-[color:var(--accent)]"
            style={{
              transform: `rotate(${i * 45}deg) translateY(${-8 - i * 2}px)`,
              animationDelay: `${i * 0.1}s`,
              opacity: 1 - i * 0.1,
            }}
          />
        ))}
      </div>
    ),
  },

  // 30. Hourglass
  {
    name: "Hourglass",
    style: "time",
    description: "Rotating hourglass shape, time-passing metaphor.",
    component: () => (
      <div className="animate-spin" style={{ animationDuration: '2s' }}>
        <div className="h-6 w-4" style={{ clipPath: 'polygon(0% 0%, 100% 0%, 50% 50%, 100% 100%, 0% 100%, 50% 50%)' }}>
          <div className="h-full w-full bg-[color:var(--accent)]" />
        </div>
      </div>
    ),
  },

  // 31. Firework
  {
    name: "Firework",
    style: "celebratory",
    description: "Bursting dots like a firework, exciting and energetic.",
    component: () => (
      <div className="relative h-12 w-12">
        {[0, 1, 2, 3, 4, 5, 6, 7, 8].map((i) => (
          <div
            key={i}
            className="absolute left-1/2 top-1/2 h-1 w-1 -translate-x-1/2 -translate-y-1/2 animate-ping rounded-full bg-[color:var(--accent)]"
            style={{
              transform: `rotate(${i * 40}deg) translateY(-${8 + i * 2}px)`,
              animationDelay: `${i * 0.05}s`,
            }}
          />
        ))}
      </div>
    ),
  },

  // 32. Metronome
  {
    name: "Metronome",
    style: "rhythmic",
    description: "Swinging like a metronome, steady rhythm.",
    component: () => (
      <div className="relative h-10 w-10">
        <div className="absolute bottom-0 left-1/2 h-8 w-0.5 -translate-x-1/2 animate-[tilt_1.5s_ease-in-out_infinite] bg-[color:var(--accent)] origin-bottom" />
        <div className="absolute top-0 left-1/2 h-2 w-2 -translate-x-1/2 animate-[tilt_1.5s_ease-in-out_infinite] rounded-full bg-[color:var(--accent)]" />
        <style jsx>{`
          @keyframes tilt {
            0%, 100% { transform: rotate(-25deg); }
            50% { transform: rotate(25deg); }
          }
        `}</style>
      </div>
    ),
  },

  // 33. Constellation
  {
    name: "Constellation",
    style: "cosmic",
    description: "Connected dots like stars, cosmic thinking theme.",
    component: () => (
      <div className="relative h-10 w-16">
        {[
          { x: 8, y: 8 },
          { x: 24, y: 4 },
          { x: 40, y: 8 },
          { x: 16, y: 16 },
          { x: 32, y: 16 },
        ].map((pos, i) => (
          <div
            key={i}
            className="absolute h-1.5 w-1.5 animate-pulse rounded-full bg-[color:var(--accent)]"
            style={{
              left: `${pos.x}px`,
              top: `${pos.y}px`,
              animationDelay: `${i * 0.2}s`,
            }}
          />
        ))}
      </div>
    ),
  },

  // 34. Liquid wave
  {
    name: "Liquid Wave",
    style: "fluid",
    description: "Smooth flowing wave, liquid-like motion.",
    component: () => (
      <div className="flex items-center gap-0.5">
        {[0, 1, 2, 3, 4, 5, 6, 7].map((i) => (
          <div
            key={i}
            className="w-1 rounded-full bg-[color:var(--accent)]"
            style={{
              height: '6px',
              animation: 'liquid 2s ease-in-out infinite',
              animationDelay: `${i * 0.1}s`,
            }}
          />
        ))}
        <style jsx>{`
          @keyframes liquid {
            0%, 100% { height: 6px; }
            25% { height: 14px; }
            50% { height: 6px; }
            75% { height: 10px; }
          }
        `}</style>
      </div>
    ),
  },

  // 35. Pixel loading
  {
    name: "Pixel Loading",
    style: "retro",
    description: "Pixelated squares appearing, retro gaming vibe.",
    component: () => (
      <div className="flex gap-1">
        {[0, 1, 2, 3].map((i) => (
          <div
            key={i}
            className="h-2 w-2 animate-pulse rounded-sm bg-[color:var(--accent)]"
            style={{ animationDelay: `${i * 0.15}s` }}
          />
        ))}
      </div>
    ),
  },

  // 36. Quantum dots
  {
    name: "Quantum Dots",
    style: "scientific",
    description: "Randomly appearing/disappearing dots, quantum uncertainty.",
    component: () => (
      <div className="flex items-center gap-2">
        {[0, 1, 2, 3, 4].map((i) => (
          <div
            key={i}
            className="h-1.5 w-1.5 animate-pulse rounded-full bg-[color:var(--accent)]"
            style={{
              animationDelay: `${i * 0.2}s`,
              animationDuration: `${1 + Math.random()}s`,
            }}
          />
        ))}
      </div>
    ),
  },

  // 37. Neon glow
  {
    name: "Neon Glow",
    style: "vibrant",
    description: "Pulsing neon effect with strong glow, vibrant and modern.",
    component: () => (
      <div className="relative">
        <div className="absolute inset-0 animate-pulse rounded-full bg-[color:var(--accent)] blur-md" style={{ animationDuration: '1.5s' }} />
        <div className="relative h-3 w-3 rounded-full bg-[color:var(--accent)]" />
      </div>
    ),
  },

  // 38. Cascading dots
  {
    name: "Cascading Dots",
    style: "flowing",
    description: "Dots cascading down like a waterfall.",
    component: () => (
      <div className="flex gap-1">
        {[0, 1, 2, 3, 4].map((i) => (
          <div
            key={i}
            className="h-2 w-2 animate-bounce rounded-full bg-[color:var(--accent)]"
            style={{
              animationDelay: `${i * 0.1}s`,
              animationDuration: '1.5s',
            }}
          />
        ))}
      </div>
    ),
  },

  // 39. Yin Yang
  {
    name: "Yin Yang",
    style: "balanced",
    description: "Rotating yin-yang pattern, balance and harmony.",
    component: () => (
      <div className="h-8 w-8 animate-spin rounded-full" style={{ animationDuration: '3s', background: `linear-gradient(90deg, var(--accent) 50%, transparent 50%)` }}>
        <div className="absolute inset-0 flex items-center justify-center">
          <div className="h-1.5 w-1.5 rounded-full bg-background" />
        </div>
      </div>
    ),
  },

  // 40. Butterfly wings
  {
    name: "Butterfly Wings",
    style: "organic",
    description: "Two dots flapping like butterfly wings.",
    component: () => (
      <div className="flex items-center gap-1">
        <div className="h-3 w-3 animate-pulse rounded-full bg-[color:var(--accent)]" style={{ animationDuration: '0.8s' }} />
        <div className="h-3 w-3 animate-pulse rounded-full bg-[color:var(--accent)]" style={{ animationDuration: '0.8s', animationDelay: '0.4s' }} />
      </div>
    ),
  },

  // 41. Matrix rain
  {
    name: "Matrix Rain",
    style: "tech",
    description: "Vertical bars like Matrix code rain.",
    component: () => (
      <div className="flex gap-1">
        {[0, 1, 2, 3, 4].map((i) => (
          <div
            key={i}
            className="w-1 rounded-full bg-[color:var(--accent)]"
            style={{
              height: '16px',
              animation: 'rain 1.5s ease-in-out infinite',
              animationDelay: `${i * 0.2}s`,
            }}
          />
        ))}
        <style jsx>{`
          @keyframes rain {
            0% { height: 0px; opacity: 0; }
            50% { height: 16px; opacity: 1; }
            100% { height: 0px; opacity: 0; }
          }
        `}</style>
      </div>
    ),
  },

  // 42. Sonar ping
  {
    name: "Sonar Ping",
    style: "tech",
    description: "Expanding circles like sonar, detection theme.",
    component: () => (
      <div className="relative h-10 w-10">
        <div className="absolute inset-0 animate-ping rounded-full border-2 border-[color:var(--accent)]" style={{ animationDuration: '2s' }} />
        <div className="absolute inset-0 animate-ping rounded-full border-2 border-[color:var(--accent)]" style={{ animationDuration: '2s', animationDelay: '0.5s' }} />
        <div className="absolute inset-0 flex items-center justify-center">
          <div className="h-2 w-2 rounded-full bg-[color:var(--accent)]" />
        </div>
      </div>
    ),
  },

  // 43. Flower bloom
  {
    name: "Flower Bloom",
    style: "organic",
    description: "Dots blooming outward like a flower opening.",
    component: () => (
      <div className="relative h-10 w-10">
        {[0, 72, 144, 216, 288].map((angle, i) => (
          <div
            key={i}
            className="absolute left-1/2 top-1/2 h-2 w-2 -translate-x-1/2 -translate-y-1/2 animate-pulse rounded-full bg-[color:var(--accent)]"
            style={{
              transform: `rotate(${angle}deg) translateY(-12px)`,
              animationDelay: `${i * 0.15}s`,
            }}
          />
        ))}
      </div>
    ),
  },

  // 44. Breathing square
  {
    name: "Breathing Square",
    style: "geometric",
    description: "Square expanding and contracting, geometric breathing.",
    component: () => (
      <div className="h-6 w-6 animate-pulse rounded bg-[color:var(--accent)]" style={{ animationDuration: '2s' }} />
    ),
  },

  // 45. Zigzag
  {
    name: "Zigzag",
    style: "dynamic",
    description: "Dots in zigzag pattern, energetic movement.",
    component: () => (
      <div className="flex items-center gap-1">
        {[0, 1, 2, 3, 4].map((i) => (
          <div
            key={i}
            className="h-2 w-2 animate-bounce rounded-full bg-[color:var(--accent)]"
            style={{
              animationDelay: `${i * 0.1}s`,
              marginTop: i % 2 === 0 ? '0' : '8px',
            }}
          />
        ))}
      </div>
    ),
  },

  // 46. Comet trail
  {
    name: "Comet Trail",
    style: "cosmic",
    description: "Dot with fading trail like a comet.",
    component: () => (
      <div className="flex items-center gap-0.5">
        {[0, 1, 2, 3, 4, 5].map((i) => (
          <div
            key={i}
            className="rounded-full bg-[color:var(--accent)]"
            style={{
              width: `${10 - i * 1.5}px`,
              height: `${10 - i * 1.5}px`,
              opacity: 1 - i * 0.15,
              animation: 'pulse 1.5s ease-in-out infinite',
              animationDelay: `${i * 0.1}s`,
            }}
          />
        ))}
      </div>
    ),
  },

  // 47. Hexagon pulse
  {
    name: "Hexagon Pulse",
    style: "geometric",
    description: "Pulsing hexagon shape, modern geometric design.",
    component: () => (
      <div className="h-6 w-6 animate-pulse" style={{ clipPath: 'polygon(50% 0%, 100% 25%, 100% 75%, 50% 100%, 0% 75%, 0% 25%)' }}>
        <div className="h-full w-full bg-[color:var(--accent)]" />
      </div>
    ),
  },

  // 48. Infinity loop
  {
    name: "Infinity Loop",
    style: "continuous",
    description: "Dot tracing infinity symbol, endless processing.",
    component: () => (
      <div className="relative h-8 w-16">
        <svg className="h-full w-full" viewBox="0 0 64 32">
          <path
            d="M 8 16 Q 16 8, 24 16 T 40 16 Q 48 24, 56 16"
            fill="none"
            stroke="currentColor"
            strokeWidth="1"
            className="text-[color:var(--accent)]/20"
          />
        </svg>
        <div className="absolute left-0 top-1/2 h-2 w-2 -translate-y-1/2 animate-[infinity_3s_ease-in-out_infinite] rounded-full bg-[color:var(--accent)]" />
        <style jsx>{`
          @keyframes infinity {
            0%, 100% { left: 8px; top: 50%; }
            25% { left: 24px; top: 30%; }
            50% { left: 40px; top: 50%; }
            75% { left: 56px; top: 70%; }
          }
        `}</style>
      </div>
    ),
  },

  // 49. Bubble float
  {
    name: "Bubble Float",
    style: "playful",
    description: "Bubbles floating upward, light and airy.",
    component: () => (
      <div className="relative h-12 w-12">
        {[0, 1, 2].map((i) => (
          <div
            key={i}
            className="absolute bottom-0 left-1/2 h-2 w-2 -translate-x-1/2 animate-[float_3s_ease-in-out_infinite] rounded-full bg-[color:var(--accent)]"
            style={{
              animationDelay: `${i * 0.8}s`,
              left: `${20 + i * 20}%`,
            }}
          />
        ))}
        <style jsx>{`
          @keyframes float {
            0% { bottom: 0; opacity: 1; }
            100% { bottom: 100%; opacity: 0; }
          }
        `}</style>
      </div>
    ),
  },

  // 50. Circuit board
  {
    name: "Circuit Board",
    style: "tech",
    description: "Dots connected like circuit paths, tech processing.",
    component: () => (
      <div className="flex items-center gap-2">
        <div className="h-2 w-2 animate-pulse rounded-full bg-[color:var(--accent)]" />
        <div className="h-0.5 w-4 animate-pulse bg-[color:var(--accent)]" style={{ animationDelay: '0.2s' }} />
        <div className="h-2 w-2 animate-pulse rounded-full bg-[color:var(--accent)]" style={{ animationDelay: '0.4s' }} />
      </div>
    ),
  },

  // 51. Diamond sparkle
  {
    name: "Diamond Sparkle",
    style: "premium",
    description: "Rotating diamond with sparkle effect, premium feel.",
    component: () => (
      <div className="relative h-6 w-6 animate-spin" style={{ animationDuration: '3s' }}>
        <div className="h-full w-full bg-[color:var(--accent)]" style={{ clipPath: 'polygon(50% 0%, 100% 50%, 50% 100%, 0% 50%)' }} />
        <div className="absolute -right-1 -top-1 h-1.5 w-1.5 animate-ping rounded-full bg-[color:var(--accent)]" />
      </div>
    ),
  },

  // 52. Waveform
  {
    name: "Waveform",
    style: "audio",
    description: "Smooth sine wave pattern, audio/voice processing.",
    component: () => (
      <div className="flex items-center gap-0.5">
        {[0, 1, 2, 3, 4, 5, 6, 7, 8].map((i) => (
          <div
            key={i}
            className="w-0.5 rounded-full bg-[color:var(--accent)]"
            style={{
              height: `${8 + Math.sin(i * 0.8) * 6}px`,
              animation: 'wave 1.5s ease-in-out infinite',
              animationDelay: `${i * 0.1}s`,
            }}
          />
        ))}
        <style jsx>{`
          @keyframes wave {
            0%, 100% { transform: scaleY(1); }
            50% { transform: scaleY(1.5); }
          }
        `}</style>
      </div>
    ),
  },

  // 53. Atom orbit
  {
    name: "Atom Orbit",
    style: "scientific",
    description: "Electrons orbiting nucleus, scientific processing.",
    component: () => (
      <div className="relative h-10 w-10">
        <div className="absolute left-1/2 top-1/2 h-2 w-2 -translate-x-1/2 -translate-y-1/2 rounded-full bg-[color:var(--accent)]" />
        <div className="absolute inset-0 animate-spin" style={{ animationDuration: '2s' }}>
          <div className="h-1.5 w-1.5 rounded-full bg-[color:var(--accent)]/60" />
        </div>
        <div className="absolute inset-0 animate-spin" style={{ animationDuration: '2s', animationDelay: '1s' }}>
          <div className="ml-auto h-1.5 w-1.5 rounded-full bg-[color:var(--accent)]/60" />
        </div>
      </div>
    ),
  },

  // 54. Shimmer
  {
    name: "Shimmer",
    style: "elegant",
    description: "Shimmering light effect passing through, elegant and subtle.",
    component: () => (
      <div className="relative h-2 w-20 overflow-hidden rounded-full bg-[color:var(--accent)]/20">
        <div className="absolute inset-y-0 w-8 animate-[shimmer_2s_ease-in-out_infinite] bg-gradient-to-r from-transparent via-[color:var(--accent)] to-transparent" />
        <style jsx>{`
          @keyframes shimmer {
            0% { left: -32px; }
            100% { left: 100%; }
          }
        `}</style>
      </div>
    ),
  },

  // 55. Kaleidoscope
  {
    name: "Kaleidoscope",
    style: "artistic",
    description: "Symmetrical rotating pattern, artistic and mesmerizing.",
    component: () => (
      <div className="relative h-10 w-10 animate-spin" style={{ animationDuration: '4s' }}>
        {[0, 90, 180, 270].map((angle, i) => (
          <div
            key={i}
            className="absolute left-1/2 top-0 h-4 w-1 -translate-x-1/2 rounded-full bg-[color:var(--accent)]"
            style={{
              transform: `rotate(${angle}deg)`,
              opacity: 0.6 + i * 0.1,
            }}
          />
        ))}
      </div>
    ),
  },
];
