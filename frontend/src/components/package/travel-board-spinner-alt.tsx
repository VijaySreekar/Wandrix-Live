"use client";

import { MapPin, Compass, Globe } from "lucide-react";

/**
 * Alternative travel-themed spinner designs
 * Import and swap in trip-board-preview.tsx to test different options
 */

// Option 1: Pulsing map pin with expanding rings
export function TravelSpinnerMapPin() {
  return (
    <div className="flex items-center justify-center">
      <div className="relative h-16 w-16">
        {/* Expanding rings */}
        <div className="absolute inset-0 animate-ping rounded-full bg-[color:var(--accent)]/20" style={{ animationDuration: '2s' }} />
        <div className="absolute inset-2 animate-ping rounded-full bg-[color:var(--accent)]/15" style={{ animationDuration: '2.5s', animationDelay: '0.3s' }} />
        
        {/* Center pin */}
        <div className="absolute inset-0 flex items-center justify-center">
          <MapPin className="h-7 w-7 text-[color:var(--accent)] animate-pulse" />
        </div>
      </div>
    </div>
  );
}

// Option 2: Rotating compass with subtle pulse
export function TravelSpinnerCompass() {
  return (
    <div className="flex items-center justify-center">
      <div className="relative h-14 w-14">
        {/* Rotating compass */}
        <div className="absolute inset-0 animate-[spin_4s_linear_infinite]">
          <Compass className="h-14 w-14 text-[color:var(--accent)]/30" />
        </div>
        
        {/* Center dot */}
        <div className="absolute inset-0 flex items-center justify-center">
          <div className="h-2 w-2 animate-pulse rounded-full bg-[color:var(--accent)]" />
        </div>
      </div>
    </div>
  );
}

// Option 3: Globe with latitude lines
export function TravelSpinnerGlobe() {
  return (
    <div className="flex items-center justify-center">
      <div className="relative h-14 w-14">
        {/* Rotating globe */}
        <div className="absolute inset-0 animate-[spin_3s_linear_infinite]">
          <Globe className="h-14 w-14 text-[color:var(--accent)]/40" />
        </div>
        
        {/* Pulsing center */}
        <div className="absolute inset-0 flex items-center justify-center">
          <div className="h-3 w-3 animate-pulse rounded-full bg-[color:var(--accent)]/60" />
        </div>
      </div>
    </div>
  );
}

// Option 4: Minimal dots forming a path
export function TravelSpinnerPath() {
  return (
    <div className="flex items-center justify-center">
      <div className="flex items-center gap-2">
        <span className="h-2 w-2 animate-pulse rounded-full bg-[color:var(--accent)]/40 [animation-delay:-0.4s]" />
        <span className="h-2.5 w-2.5 animate-pulse rounded-full bg-[color:var(--accent)]/60 [animation-delay:-0.2s]" />
        <span className="h-3 w-3 animate-pulse rounded-full bg-[color:var(--accent)]" />
        <span className="h-2.5 w-2.5 animate-pulse rounded-full bg-[color:var(--accent)]/60 [animation-delay:0.2s]" />
        <span className="h-2 w-2 animate-pulse rounded-full bg-[color:var(--accent)]/40 [animation-delay:0.4s]" />
      </div>
    </div>
  );
}

// Option 5: Destination marker with wave effect
export function TravelSpinnerDestination() {
  return (
    <div className="flex items-center justify-center">
      <div className="relative h-16 w-16">
        {/* Ripple waves */}
        <div className="absolute inset-0">
          <div className="absolute inset-0 animate-ping rounded-full border-2 border-[color:var(--accent)]/30" style={{ animationDuration: '2s' }} />
          <div className="absolute inset-0 animate-ping rounded-full border-2 border-[color:var(--accent)]/20" style={{ animationDuration: '2s', animationDelay: '0.5s' }} />
        </div>
        
        {/* Center marker */}
        <div className="absolute inset-0 flex items-center justify-center">
          <div className="flex h-4 w-4 items-center justify-center rounded-full bg-[color:var(--accent)]">
            <div className="h-1.5 w-1.5 rounded-full bg-white" />
          </div>
        </div>
      </div>
    </div>
  );
}
