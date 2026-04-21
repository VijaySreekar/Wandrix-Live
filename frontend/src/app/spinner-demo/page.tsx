"use client";

import { MapPin, Compass, Globe, Plane, Navigation, Map } from "lucide-react";
import {
  moreTravelSpinners,
  TravelSpinnerAnimationStyles,
} from "@/components/spinner-demo/more-travel-spinners";

export default function SpinnerDemoPage() {
  return (
    <div className="min-h-screen bg-background p-8">
      <TravelSpinnerAnimationStyles />
      <div className="mx-auto max-w-7xl">
        <h1 className="mb-4 text-3xl font-semibold text-foreground">
          Spinner Demo
        </h1>
        <p className="mb-12 max-w-2xl text-sm leading-7 text-foreground/60">
          130 loading studies, including 50 additional travel-themed motion
          patterns. Click any spinner card to copy its number.
        </p>
        
        <div className="grid grid-cols-2 gap-6 md:grid-cols-3 lg:grid-cols-5">
          {allSpinners.map((Spinner, index) => (
            <div
              key={index}
              className="flex flex-col items-center gap-3 rounded-xl border border-border bg-card p-6 transition-all hover:border-[color:var(--accent)] hover:shadow-lg cursor-pointer"
              onClick={() => {
                navigator.clipboard.writeText(`#${index + 1}`);
                alert(`Copied: Spinner #${index + 1}`);
              }}
            >
              <div className="flex h-24 w-full items-center justify-center">
                <Spinner />
              </div>
              <span className="text-xs font-medium text-foreground/50">
                #{index + 1}
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

// 50 Different Spinner Animations
const spinners = [
  // 1. Classic ring spinner
  () => (
    <div className="relative h-12 w-12">
      <div className="absolute inset-0 rounded-full border-2 border-[color:var(--accent)]/20" />
      <div className="absolute inset-0 animate-spin">
        <div className="h-full w-full rounded-full border-2 border-transparent border-t-[color:var(--accent)]" />
      </div>
    </div>
  ),

  // 2. Double ring
  () => (
    <div className="relative h-12 w-12">
      <div className="absolute inset-0 animate-spin">
        <div className="h-full w-full rounded-full border-2 border-transparent border-t-[color:var(--accent)]" />
      </div>
      <div className="absolute inset-2 animate-spin" style={{ animationDirection: 'reverse' }}>
        <div className="h-full w-full rounded-full border-2 border-transparent border-t-[color:var(--accent)]/50" />
      </div>
    </div>
  ),

  // 3. Pulsing ring
  () => (
    <div className="h-12 w-12 animate-pulse rounded-full border-4 border-[color:var(--accent)]" />
  ),

  // 4. Three dots wave
  () => (
    <div className="flex gap-2">
      <div className="h-3 w-3 animate-bounce rounded-full bg-[color:var(--accent)] [animation-delay:-0.3s]" />
      <div className="h-3 w-3 animate-bounce rounded-full bg-[color:var(--accent)] [animation-delay:-0.15s]" />
      <div className="h-3 w-3 animate-bounce rounded-full bg-[color:var(--accent)]" />
    </div>
  ),

  // 5. Five dots pulse
  () => (
    <div className="flex gap-1.5">
      {[0, 1, 2, 3, 4].map((i) => (
        <div
          key={i}
          className="h-2 w-2 animate-pulse rounded-full bg-[color:var(--accent)]"
          style={{ animationDelay: `${i * 0.15}s` }}
        />
      ))}
    </div>
  ),

  // 6. Map pin with rings
  () => (
    <div className="relative h-16 w-16">
      <div className="absolute inset-0 animate-ping rounded-full bg-[color:var(--accent)]/20" />
      <div className="absolute inset-0 flex items-center justify-center">
        <MapPin className="h-7 w-7 animate-pulse text-[color:var(--accent)]" />
      </div>
    </div>
  ),

  // 7. Rotating compass
  () => (
    <div className="animate-spin">
      <Compass className="h-12 w-12 text-[color:var(--accent)]" style={{ animationDuration: '3s' }} />
    </div>
  ),

  // 8. Spinning globe
  () => (
    <div className="animate-spin" style={{ animationDuration: '2s' }}>
      <Globe className="h-12 w-12 text-[color:var(--accent)]" />
    </div>
  ),

  // 9. Bars growing
  () => (
    <div className="flex items-end gap-1">
      {[0, 1, 2, 3].map((i) => (
        <div
          key={i}
          className="w-2 animate-pulse bg-[color:var(--accent)]"
          style={{
            height: '24px',
            animationDelay: `${i * 0.15}s`,
          }}
        />
      ))}
    </div>
  ),

  // 10. Square rotation
  () => (
    <div className="h-12 w-12 animate-spin rounded-lg bg-[color:var(--accent)]" />
  ),

  // 11. Diamond rotation
  () => (
    <div className="h-12 w-12 animate-spin bg-[color:var(--accent)]" style={{ transform: 'rotate(45deg)' }} />
  ),

  // 12. Gradient ring
  () => (
    <div className="relative h-12 w-12">
      <div className="absolute inset-0 animate-spin rounded-full bg-gradient-to-tr from-[color:var(--accent)] to-transparent" />
      <div className="absolute inset-1 rounded-full bg-background" />
    </div>
  ),

  // 13. Dashed ring
  () => (
    <div className="h-12 w-12 animate-spin rounded-full border-4 border-dashed border-[color:var(--accent)]" />
  ),

  // 14. Dotted ring
  () => (
    <div className="h-12 w-12 animate-spin rounded-full border-4 border-dotted border-[color:var(--accent)]" />
  ),

  // 15. Expanding circle
  () => (
    <div className="relative h-12 w-12">
      <div className="absolute inset-0 animate-ping rounded-full bg-[color:var(--accent)]/40" />
    </div>
  ),

  // 16. Double ping
  () => (
    <div className="relative h-12 w-12">
      <div className="absolute inset-0 animate-ping rounded-full bg-[color:var(--accent)]/30" />
      <div className="absolute inset-0 animate-ping rounded-full bg-[color:var(--accent)]/30" style={{ animationDelay: '0.5s' }} />
      <div className="absolute inset-0 flex items-center justify-center">
        <div className="h-3 w-3 rounded-full bg-[color:var(--accent)]" />
      </div>
    </div>
  ),

  // 17. Orbit dots
  () => (
    <div className="relative h-12 w-12">
      <div className="absolute inset-0 animate-spin">
        <div className="h-2 w-2 rounded-full bg-[color:var(--accent)]" />
      </div>
      <div className="absolute inset-0 animate-spin" style={{ animationDelay: '0.5s' }}>
        <div className="h-2 w-2 rounded-full bg-[color:var(--accent)]/50" style={{ marginLeft: 'auto' }} />
      </div>
    </div>
  ),

  // 18. Plane icon pulse
  () => (
    <Plane className="h-10 w-10 animate-pulse text-[color:var(--accent)]" />
  ),

  // 19. Navigation pulse
  () => (
    <Navigation className="h-10 w-10 animate-pulse text-[color:var(--accent)]" />
  ),

  // 20. Map pulse
  () => (
    <Map className="h-10 w-10 animate-pulse text-[color:var(--accent)]" />
  ),

  // 21. Thin ring spin
  () => (
    <div className="h-12 w-12 animate-spin rounded-full border border-transparent border-t-[color:var(--accent)]" />
  ),

  // 22. Thick ring spin
  () => (
    <div className="h-12 w-12 animate-spin rounded-full border-4 border-transparent border-t-[color:var(--accent)]" />
  ),

  // 23. Half ring spin
  () => (
    <div className="h-12 w-12 animate-spin rounded-full border-2 border-transparent border-l-[color:var(--accent)] border-t-[color:var(--accent)]" />
  ),

  // 24. Three quarter ring
  () => (
    <div className="h-12 w-12 animate-spin rounded-full border-2 border-[color:var(--accent)] border-b-transparent" />
  ),

  // 25. Pulsing square
  () => (
    <div className="h-10 w-10 animate-pulse rounded bg-[color:var(--accent)]" />
  ),

  // 26. Bouncing dot
  () => (
    <div className="h-4 w-4 animate-bounce rounded-full bg-[color:var(--accent)]" />
  ),

  // 27. Scale pulse
  () => (
    <div className="h-8 w-8 animate-ping rounded-full bg-[color:var(--accent)]" />
  ),

  // 28. Horizontal bars
  () => (
    <div className="flex flex-col gap-1.5">
      {[0, 1, 2].map((i) => (
        <div
          key={i}
          className="h-1.5 w-12 animate-pulse rounded-full bg-[color:var(--accent)]"
          style={{ animationDelay: `${i * 0.2}s` }}
        />
      ))}
    </div>
  ),

  // 29. Vertical bars
  () => (
    <div className="flex gap-1.5">
      {[0, 1, 2].map((i) => (
        <div
          key={i}
          className="h-12 w-1.5 animate-pulse rounded-full bg-[color:var(--accent)]"
          style={{ animationDelay: `${i * 0.2}s` }}
        />
      ))}
    </div>
  ),

  // 30. Corner dots
  () => (
    <div className="relative h-12 w-12">
      <div className="absolute left-0 top-0 h-2 w-2 animate-ping rounded-full bg-[color:var(--accent)]" />
      <div className="absolute right-0 top-0 h-2 w-2 animate-ping rounded-full bg-[color:var(--accent)]" style={{ animationDelay: '0.25s' }} />
      <div className="absolute bottom-0 right-0 h-2 w-2 animate-ping rounded-full bg-[color:var(--accent)]" style={{ animationDelay: '0.5s' }} />
      <div className="absolute bottom-0 left-0 h-2 w-2 animate-ping rounded-full bg-[color:var(--accent)]" style={{ animationDelay: '0.75s' }} />
    </div>
  ),

  // 31. Ripple effect
  () => (
    <div className="relative h-12 w-12">
      {[0, 1, 2].map((i) => (
        <div
          key={i}
          className="absolute inset-0 animate-ping rounded-full border-2 border-[color:var(--accent)]"
          style={{ animationDelay: `${i * 0.4}s`, animationDuration: '1.5s' }}
        />
      ))}
    </div>
  ),

  // 32. Slow spin
  () => (
    <div className="h-12 w-12 animate-spin rounded-full border-2 border-transparent border-t-[color:var(--accent)]" style={{ animationDuration: '3s' }} />
  ),

  // 33. Fast spin
  () => (
    <div className="h-12 w-12 animate-spin rounded-full border-2 border-transparent border-t-[color:var(--accent)]" style={{ animationDuration: '0.6s' }} />
  ),

  // 34. Reverse spin
  () => (
    <div className="h-12 w-12 animate-spin rounded-full border-2 border-transparent border-t-[color:var(--accent)]" style={{ animationDirection: 'reverse' }} />
  ),

  // 35. Growing dots
  () => (
    <div className="flex gap-2">
      {[0, 1, 2].map((i) => (
        <div
          key={i}
          className="animate-ping rounded-full bg-[color:var(--accent)]"
          style={{
            width: `${8 + i * 4}px`,
            height: `${8 + i * 4}px`,
            animationDelay: `${i * 0.2}s`,
          }}
        />
      ))}
    </div>
  ),

  // 36. Circle with dot
  () => (
    <div className="relative h-12 w-12">
      <div className="absolute inset-0 rounded-full border-2 border-[color:var(--accent)]/30" />
      <div className="absolute inset-0 animate-spin">
        <div className="h-2 w-2 rounded-full bg-[color:var(--accent)]" />
      </div>
    </div>
  ),

  // 37. Dual orbit
  () => (
    <div className="relative h-12 w-12">
      <div className="absolute inset-0 animate-spin" style={{ animationDuration: '2s' }}>
        <div className="h-2 w-2 rounded-full bg-[color:var(--accent)]" />
      </div>
      <div className="absolute inset-0 animate-spin" style={{ animationDuration: '2s', animationDirection: 'reverse' }}>
        <div className="ml-auto h-2 w-2 rounded-full bg-[color:var(--accent)]/60" />
      </div>
    </div>
  ),

  // 38. Fade pulse
  () => (
    <div className="h-10 w-10 animate-pulse rounded-full bg-[color:var(--accent)]" style={{ animationDuration: '1.5s' }} />
  ),

  // 39. Border pulse
  () => (
    <div className="h-12 w-12 animate-pulse rounded-full border-4 border-[color:var(--accent)]" />
  ),

  // 40. Gradient spin
  () => (
    <div className="relative h-12 w-12 animate-spin">
      <div className="h-full w-full rounded-full bg-gradient-to-r from-[color:var(--accent)] via-[color:var(--accent)]/50 to-transparent" />
      <div className="absolute inset-1 rounded-full bg-background" />
    </div>
  ),

  // 41. Staggered squares
  () => (
    <div className="grid grid-cols-2 gap-1">
      {[0, 1, 2, 3].map((i) => (
        <div
          key={i}
          className="h-4 w-4 animate-pulse rounded bg-[color:var(--accent)]"
          style={{ animationDelay: `${i * 0.15}s` }}
        />
      ))}
    </div>
  ),

  // 42. Line scan
  () => (
    <div className="relative h-12 w-12">
      <div className="absolute inset-x-0 top-0 h-0.5 animate-bounce bg-[color:var(--accent)]" />
    </div>
  ),

  // 43. Circular dots
  () => (
    <div className="relative h-12 w-12">
      {[0, 1, 2, 3, 4, 5, 6, 7].map((i) => (
        <div
          key={i}
          className="absolute left-1/2 top-0 h-1.5 w-1.5 -translate-x-1/2 animate-pulse rounded-full bg-[color:var(--accent)]"
          style={{
            transform: `rotate(${i * 45}deg) translateY(20px)`,
            animationDelay: `${i * 0.125}s`,
          }}
        />
      ))}
    </div>
  ),

  // 44. Cross spin
  () => (
    <div className="relative h-12 w-12 animate-spin">
      <div className="absolute left-1/2 top-0 h-full w-0.5 -translate-x-1/2 bg-[color:var(--accent)]" />
      <div className="absolute left-0 top-1/2 h-0.5 w-full -translate-y-1/2 bg-[color:var(--accent)]" />
    </div>
  ),

  // 45. Hexagon spin
  () => (
    <div className="h-10 w-10 animate-spin" style={{ clipPath: 'polygon(50% 0%, 100% 25%, 100% 75%, 50% 100%, 0% 75%, 0% 25%)' }}>
      <div className="h-full w-full bg-[color:var(--accent)]" />
    </div>
  ),

  // 46. Triangle spin
  () => (
    <div className="h-10 w-10 animate-spin" style={{ clipPath: 'polygon(50% 0%, 0% 100%, 100% 100%)' }}>
      <div className="h-full w-full bg-[color:var(--accent)]" />
    </div>
  ),

  // 47. Destination marker
  () => (
    <div className="relative h-16 w-16">
      <div className="absolute inset-0 animate-ping rounded-full border-2 border-[color:var(--accent)]/30" style={{ animationDuration: '2s' }} />
      <div className="absolute inset-0 flex items-center justify-center">
        <div className="flex h-4 w-4 items-center justify-center rounded-full bg-[color:var(--accent)]">
          <div className="h-1.5 w-1.5 rounded-full bg-white" />
        </div>
      </div>
    </div>
  ),

  // 48. Radar sweep
  () => (
    <div className="relative h-12 w-12">
      <div className="absolute inset-0 rounded-full border-2 border-[color:var(--accent)]/20" />
      <div className="absolute inset-0 animate-spin" style={{ animationDuration: '2s' }}>
        <div className="h-full w-1/2 origin-right bg-gradient-to-r from-transparent to-[color:var(--accent)]/40" style={{ borderRadius: '100% 0 0 100%' }} />
      </div>
    </div>
  ),

  // 49. Breathing circle
  () => (
    <div className="h-10 w-10 animate-pulse rounded-full bg-[color:var(--accent)]/60" style={{ animationDuration: '2s' }} />
  ),

  // 50. Multi-ring
  () => (
    <div className="relative h-12 w-12">
      <div className="absolute inset-0 animate-spin rounded-full border-2 border-transparent border-t-[color:var(--accent)]" />
      <div className="absolute inset-1 animate-spin rounded-full border-2 border-transparent border-t-[color:var(--accent)]/70" style={{ animationDuration: '1.5s' }} />
      <div className="absolute inset-2 animate-spin rounded-full border-2 border-transparent border-t-[color:var(--accent)]/40" style={{ animationDuration: '1s' }} />
    </div>
  ),

  // 51. Flight path arc
  () => (
    <div className="relative h-12 w-16">
      <svg className="h-full w-full" viewBox="0 0 64 48">
        <path
          d="M 8 40 Q 32 8, 56 40"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeDasharray="4 4"
          className="text-[color:var(--accent)]/30"
        />
      </svg>
      <div className="absolute left-0 top-0 h-full w-full">
        <div className="animate-[flight_2s_ease-in-out_infinite]">
          <Plane className="h-4 w-4 text-[color:var(--accent)]" style={{ transform: 'rotate(-45deg)' }} />
        </div>
      </div>
      <style jsx>{`
        @keyframes flight {
          0% { transform: translate(8px, 40px); }
          50% { transform: translate(32px, 8px); }
          100% { transform: translate(56px, 40px); }
        }
      `}</style>
    </div>
  ),

  // 52. Compass needle
  () => (
    <div className="relative h-14 w-14">
      <Compass className="h-14 w-14 text-[color:var(--accent)]/20" />
      <div className="absolute inset-0 flex items-center justify-center">
        <div className="h-6 w-0.5 animate-[swing_2s_ease-in-out_infinite] rounded-full bg-[color:var(--accent)] origin-bottom" />
      </div>
      <style jsx>{`
        @keyframes swing {
          0%, 100% { transform: rotate(-20deg); }
          50% { transform: rotate(20deg); }
        }
      `}</style>
    </div>
  ),

  // 53. Location ping sequence
  () => (
    <div className="relative h-14 w-14">
      {[0, 1, 2].map((i) => (
        <div
          key={i}
          className="absolute inset-0 animate-ping rounded-full"
          style={{
            border: '2px solid var(--accent)',
            opacity: 0.3,
            animationDelay: `${i * 0.6}s`,
            animationDuration: '2s',
          }}
        />
      ))}
      <div className="absolute inset-0 flex items-center justify-center">
        <MapPin className="h-6 w-6 text-[color:var(--accent)]" />
      </div>
    </div>
  ),

  // 54. Globe latitude spin
  () => (
    <div className="relative h-14 w-14">
      <Globe className="h-14 w-14 text-[color:var(--accent)]/25" />
      <div className="absolute inset-0 flex items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-transparent border-t-[color:var(--accent)]" style={{ animationDuration: '1.5s' }} />
      </div>
    </div>
  ),

  // 55. Journey dots trail
  () => (
    <div className="flex items-center gap-1">
      {[0, 1, 2, 3, 4, 5, 6].map((i) => (
        <div
          key={i}
          className="rounded-full bg-[color:var(--accent)]"
          style={{
            width: `${4 + Math.sin(i * 0.5) * 2}px`,
            height: `${4 + Math.sin(i * 0.5) * 2}px`,
            opacity: 0.3 + (i / 6) * 0.7,
            animation: 'pulse 1.5s ease-in-out infinite',
            animationDelay: `${i * 0.1}s`,
          }}
        />
      ))}
    </div>
  ),

  // 56. Rotating waypoints
  () => (
    <div className="relative h-14 w-14">
      <div className="absolute inset-0 animate-spin" style={{ animationDuration: '3s' }}>
        {[0, 1, 2, 3].map((i) => (
          <div
            key={i}
            className="absolute h-2 w-2 rounded-full bg-[color:var(--accent)]"
            style={{
              top: '50%',
              left: '50%',
              transform: `rotate(${i * 90}deg) translateY(-20px) translateX(-4px)`,
            }}
          />
        ))}
      </div>
      <div className="absolute inset-0 flex items-center justify-center">
        <div className="h-3 w-3 rounded-full bg-[color:var(--accent)]" />
      </div>
    </div>
  ),

  // 57. Pulsing route line
  () => (
    <div className="relative h-2 w-16">
      <div className="h-full w-full rounded-full bg-[color:var(--accent)]/20" />
      <div className="absolute inset-0 animate-[expand_1.5s_ease-in-out_infinite] rounded-full bg-[color:var(--accent)]" />
      <style jsx>{`
        @keyframes expand {
          0%, 100% { width: 20%; left: 0; }
          50% { width: 100%; left: 0; }
        }
      `}</style>
    </div>
  ),

  // 58. Destination beacon
  () => (
    <div className="relative h-16 w-16">
      <div className="absolute inset-0 flex items-center justify-center">
        <div className="h-3 w-3 rounded-full bg-[color:var(--accent)]" />
      </div>
      {[0, 1, 2, 3].map((i) => (
        <div
          key={i}
          className="absolute inset-0 animate-ping rounded-full border border-[color:var(--accent)]"
          style={{
            animationDelay: `${i * 0.4}s`,
            animationDuration: '2s',
          }}
        />
      ))}
    </div>
  ),

  // 59. Travel card flip
  () => (
    <div className="animate-[flip_2s_ease-in-out_infinite]">
      <div className="h-10 w-14 rounded-lg bg-[color:var(--accent)]" />
      <style jsx>{`
        @keyframes flip {
          0%, 100% { transform: rotateY(0deg); }
          50% { transform: rotateY(180deg); }
        }
      `}</style>
    </div>
  ),

  // 60. Orbit trail
  () => (
    <div className="relative h-14 w-14">
      <div className="absolute inset-0 rounded-full border border-dashed border-[color:var(--accent)]/20" />
      <div className="absolute inset-0 animate-spin" style={{ animationDuration: '2s' }}>
        <div className="flex h-full items-center">
          <div className="h-2 w-2 rounded-full bg-[color:var(--accent)]" />
        </div>
      </div>
      <div className="absolute inset-0 animate-spin" style={{ animationDuration: '2s', animationDelay: '0.3s' }}>
        <div className="flex h-full items-center">
          <div className="h-1.5 w-1.5 rounded-full bg-[color:var(--accent)]/60" />
        </div>
      </div>
    </div>
  ),

  // 61. Map unfold
  () => (
    <div className="relative h-12 w-12 overflow-hidden">
      <Map className="h-12 w-12 animate-[unfold_2s_ease-in-out_infinite] text-[color:var(--accent)]" />
      <style jsx>{`
        @keyframes unfold {
          0%, 100% { transform: scaleX(0.3); opacity: 0.5; }
          50% { transform: scaleX(1); opacity: 1; }
        }
      `}</style>
    </div>
  ),

  // 62. Navigation arrow spin
  () => (
    <div className="animate-spin" style={{ animationDuration: '2s' }}>
      <Navigation className="h-10 w-10 text-[color:var(--accent)]" />
    </div>
  ),

  // 63. Ticket scan
  () => (
    <div className="relative h-10 w-14">
      <div className="h-full w-full rounded border-2 border-[color:var(--accent)]/30" />
      <div className="absolute inset-0 overflow-hidden rounded">
        <div className="h-0.5 w-full animate-[scan_2s_ease-in-out_infinite] bg-[color:var(--accent)]" />
      </div>
      <style jsx>{`
        @keyframes scan {
          0%, 100% { transform: translateY(0); }
          50% { transform: translateY(40px); }
        }
      `}</style>
    </div>
  ),

  // 64. Layered rings
  () => (
    <div className="relative h-14 w-14">
      {[0, 1, 2].map((i) => (
        <div
          key={i}
          className="absolute animate-spin rounded-full border-2 border-transparent"
          style={{
            inset: `${i * 4}px`,
            borderTopColor: 'var(--accent)',
            opacity: 1 - i * 0.3,
            animationDuration: `${1.5 + i * 0.5}s`,
            animationDirection: i % 2 === 0 ? 'normal' : 'reverse',
          }}
        />
      ))}
    </div>
  ),

  // 65. Pulse wave
  () => (
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
          0%, 100% { height: 8px; }
          50% { height: 24px; }
        }
      `}</style>
    </div>
  ),

  // 66. Spiral dots
  () => (
    <div className="relative h-14 w-14">
      {[0, 1, 2, 3, 4, 5].map((i) => (
        <div
          key={i}
          className="absolute left-1/2 top-1/2 h-2 w-2 -translate-x-1/2 -translate-y-1/2 animate-pulse rounded-full bg-[color:var(--accent)]"
          style={{
            transform: `rotate(${i * 60}deg) translateY(${-12 - i * 2}px)`,
            animationDelay: `${i * 0.15}s`,
            opacity: 1 - i * 0.12,
          }}
        />
      ))}
    </div>
  ),

  // 67. Boarding pass slide
  () => (
    <div className="relative h-8 w-16 overflow-hidden rounded border border-[color:var(--accent)]/30">
      <div className="absolute inset-0 animate-[slide_2s_ease-in-out_infinite] bg-[color:var(--accent)]/20" />
      <style jsx>{`
        @keyframes slide {
          0%, 100% { transform: translateX(-100%); }
          50% { transform: translateX(100%); }
        }
      `}</style>
    </div>
  ),

  // 68. Concentric pulse
  () => (
    <div className="relative h-14 w-14">
      {[0, 1, 2, 3].map((i) => (
        <div
          key={i}
          className="absolute rounded-full border-2 border-[color:var(--accent)]"
          style={{
            inset: `${i * 3}px`,
            animation: 'pulse 2s ease-in-out infinite',
            animationDelay: `${i * 0.2}s`,
          }}
        />
      ))}
    </div>
  ),

  // 69. Route connector
  () => (
    <div className="flex items-center gap-2">
      <div className="h-3 w-3 animate-pulse rounded-full bg-[color:var(--accent)]" />
      <div className="h-0.5 w-8 animate-pulse rounded-full bg-[color:var(--accent)]/50" style={{ animationDelay: '0.2s' }} />
      <div className="h-3 w-3 animate-pulse rounded-full bg-[color:var(--accent)]" style={{ animationDelay: '0.4s' }} />
    </div>
  ),

  // 70. Elevation dots
  () => (
    <div className="flex items-end gap-1.5">
      {[0, 1, 2, 3, 4, 3, 2, 1].map((height, i) => (
        <div
          key={i}
          className="w-1.5 animate-pulse rounded-full bg-[color:var(--accent)]"
          style={{
            height: `${height * 3 + 4}px`,
            animationDelay: `${i * 0.1}s`,
          }}
        />
      ))}
    </div>
  ),

  // 71. Crosshair focus
  () => (
    <div className="relative h-12 w-12">
      <div className="absolute inset-0 animate-ping rounded-full border-2 border-[color:var(--accent)]/40" />
      <div className="absolute left-1/2 top-0 h-full w-0.5 -translate-x-1/2 bg-[color:var(--accent)]/30" />
      <div className="absolute left-0 top-1/2 h-0.5 w-full -translate-y-1/2 bg-[color:var(--accent)]/30" />
      <div className="absolute inset-0 flex items-center justify-center">
        <div className="h-2 w-2 animate-pulse rounded-full bg-[color:var(--accent)]" />
      </div>
    </div>
  ),

  // 72. Plane takeoff
  () => (
    <div className="relative h-12 w-16">
      <div className="animate-[takeoff_2s_ease-in-out_infinite]">
        <Plane className="h-5 w-5 text-[color:var(--accent)]" />
      </div>
      <style jsx>{`
        @keyframes takeoff {
          0% { transform: translate(0, 12px) rotate(0deg); opacity: 0.5; }
          50% { transform: translate(24px, 0) rotate(-20deg); opacity: 1; }
          100% { transform: translate(48px, -8px) rotate(-35deg); opacity: 0.5; }
        }
      `}</style>
    </div>
  ),

  // 73. Hexagon orbit
  () => (
    <div className="relative h-14 w-14">
      <div className="absolute inset-0 animate-spin" style={{ animationDuration: '3s' }}>
        <div
          className="h-full w-full border-2 border-[color:var(--accent)]/30"
          style={{ clipPath: 'polygon(50% 0%, 100% 25%, 100% 75%, 50% 100%, 0% 75%, 0% 25%)' }}
        />
      </div>
      <div className="absolute inset-0 flex items-center justify-center">
        <div className="h-2 w-2 animate-pulse rounded-full bg-[color:var(--accent)]" />
      </div>
    </div>
  ),

  // 74. Smooth arc
  () => (
    <div className="relative h-12 w-12">
      <svg className="h-full w-full -rotate-90" viewBox="0 0 48 48">
        <circle
          cx="24"
          cy="24"
          r="20"
          fill="none"
          stroke="currentColor"
          strokeWidth="3"
          strokeDasharray="125.6"
          strokeDashoffset="0"
          className="animate-[draw_2s_ease-in-out_infinite] text-[color:var(--accent)]"
        />
      </svg>
      <style jsx>{`
        @keyframes draw {
          0% { stroke-dashoffset: 125.6; }
          50% { stroke-dashoffset: 0; }
          100% { stroke-dashoffset: -125.6; }
        }
      `}</style>
    </div>
  ),

  // 75. Dual pulse
  () => (
    <div className="relative h-12 w-12">
      <div className="absolute inset-0 animate-ping rounded-full bg-[color:var(--accent)]/30" />
      <div className="absolute inset-2 animate-ping rounded-full bg-[color:var(--accent)]/40" style={{ animationDelay: '0.5s' }} />
      <div className="absolute inset-0 flex items-center justify-center">
        <div className="h-4 w-4 rounded-full bg-[color:var(--accent)]" />
      </div>
    </div>
  ),

  // 76. Zigzag path
  () => (
    <div className="relative h-10 w-16">
      <svg className="h-full w-full" viewBox="0 0 64 40">
        <path
          d="M 4 20 L 16 8 L 28 20 L 40 8 L 52 20 L 60 12"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeDasharray="4 4"
          className="animate-[dash_2s_linear_infinite] text-[color:var(--accent)]/40"
        />
      </svg>
      <style jsx>{`
        @keyframes dash {
          to { stroke-dashoffset: -16; }
        }
      `}</style>
    </div>
  ),

  // 77. Spinning ticket
  () => (
    <div className="animate-[spinY_2s_ease-in-out_infinite]">
      <div className="h-8 w-12 rounded border-2 border-[color:var(--accent)] bg-[color:var(--accent)]/10" />
      <style jsx>{`
        @keyframes spinY {
          0%, 100% { transform: rotateY(0deg); }
          50% { transform: rotateY(180deg); }
        }
      `}</style>
    </div>
  ),

  // 78. Radar ping
  () => (
    <div className="relative h-14 w-14">
      <div className="absolute inset-0 rounded-full border-2 border-[color:var(--accent)]/20" />
      <div className="absolute inset-0 animate-spin" style={{ animationDuration: '2s' }}>
        <div className="h-full w-full origin-center bg-gradient-to-r from-[color:var(--accent)]/40 to-transparent" style={{ clipPath: 'polygon(50% 50%, 50% 0%, 100% 50%)' }} />
      </div>
      <div className="absolute inset-0 flex items-center justify-center">
        <div className="h-2 w-2 rounded-full bg-[color:var(--accent)]" />
      </div>
    </div>
  ),

  // 79. Staggered orbit
  () => (
    <div className="relative h-14 w-14">
      {[0, 1, 2].map((i) => (
        <div
          key={i}
          className="absolute inset-0 animate-spin"
          style={{
            animationDuration: `${2 + i * 0.5}s`,
            animationDirection: i % 2 === 0 ? 'normal' : 'reverse',
          }}
        >
          <div
            className="h-2 w-2 rounded-full bg-[color:var(--accent)]"
            style={{ opacity: 1 - i * 0.25 }}
          />
        </div>
      ))}
    </div>
  ),

  // 80. Loading bar travel
  () => (
    <div className="relative h-2 w-20 overflow-hidden rounded-full bg-[color:var(--accent)]/20">
      <div className="absolute inset-y-0 left-0 w-1/3 animate-[travel_1.5s_ease-in-out_infinite] rounded-full bg-[color:var(--accent)]" />
      <style jsx>{`
        @keyframes travel {
          0% { left: -33.33%; }
          100% { left: 100%; }
        }
      `}</style>
    </div>
  ),
];

const allSpinners = [...spinners, ...moreTravelSpinners];
