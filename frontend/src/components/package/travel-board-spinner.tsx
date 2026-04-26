"use client";

export function TravelBoardSpinner() {
  return (
    <div className="flex items-center justify-center">
      {/* Pulsing ring loader */}
      <div className="relative h-12 w-12">
        {/* Outer ring */}
        <div className="absolute inset-0 rounded-full border-2 border-[color:var(--accent)]/20" />
        
        {/* Animated ring */}
        <div className="absolute inset-0 animate-[spin_1.2s_cubic-bezier(0.4,0,0.2,1)_infinite]">
          <div className="h-full w-full rounded-full border-2 border-transparent border-t-[color:var(--accent)]" />
        </div>
        
        {/* Inner pulse */}
        <div className="absolute inset-2 animate-pulse rounded-full bg-[color:var(--accent)]/10" />
      </div>
    </div>
  );
}
