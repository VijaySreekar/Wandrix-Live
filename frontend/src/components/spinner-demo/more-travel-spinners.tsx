"use client";

import type { JSX } from "react";
import type { LucideIcon } from "lucide-react";
import {
  BusFront,
  CableCar,
  Camera,
  CarFront,
  Coffee,
  Compass,
  Globe,
  Hotel,
  Luggage,
  Map,
  MapPin,
  Mountain,
  Navigation,
  Plane,
  Route,
  Ship,
  ShipWheel,
  Sun,
  Ticket,
  TicketsPlane,
  TrainFront,
  Trees,
  UtensilsCrossed,
  Waves,
} from "lucide-react";

type SpinnerComponent = () => JSX.Element;

type IconSpinnerConfig = {
  Icon: LucideIcon;
  duration: number;
  reverse?: boolean;
  rings?: number;
};

type LaneSpinnerConfig = {
  Icon: LucideIcon;
  duration: number;
  reverse?: boolean;
};

type PanelSpinnerConfig = {
  Icon: LucideIcon;
  duration: number;
  delay?: number;
};

export function TravelSpinnerAnimationStyles() {
  return (
    <style jsx global>{`
      @keyframes spinner-demo-lane {
        0% {
          transform: translateX(-18%) translateY(0);
        }

        50% {
          transform: translateX(118%) translateY(-5px);
        }

        100% {
          transform: translateX(-18%) translateY(0);
        }
      }

      @keyframes spinner-demo-lane-reverse {
        0% {
          transform: translateX(118%) translateY(0);
        }

        50% {
          transform: translateX(-18%) translateY(-5px);
        }

        100% {
          transform: translateX(118%) translateY(0);
        }
      }

      @keyframes spinner-demo-shutter {
        0%,
        100% {
          transform: scaleX(0.3);
          opacity: 0.42;
        }

        50% {
          transform: scaleX(1);
          opacity: 1;
        }
      }

      @keyframes spinner-demo-bob {
        0%,
        100% {
          transform: translateY(0);
        }

        50% {
          transform: translateY(-4px);
        }
      }
    `}</style>
  );
}

const haloConfigs: IconSpinnerConfig[] = [
  { Icon: Plane, duration: 1.8, rings: 2 },
  { Icon: TrainFront, duration: 2.1, rings: 3 },
  { Icon: BusFront, duration: 2.3, rings: 2 },
  { Icon: Hotel, duration: 2.4, rings: 3 },
  { Icon: Luggage, duration: 2.0, rings: 2 },
  { Icon: Ticket, duration: 1.9, rings: 3 },
  { Icon: Ship, duration: 2.5, rings: 2 },
  { Icon: Camera, duration: 2.2, rings: 3 },
  { Icon: Coffee, duration: 1.7, rings: 2 },
  { Icon: Trees, duration: 2.6, rings: 3 },
];

const orbitConfigs: IconSpinnerConfig[] = [
  { Icon: Compass, duration: 2.6 },
  { Icon: Globe, duration: 2.2, reverse: true },
  { Icon: MapPin, duration: 2.8 },
  { Icon: Route, duration: 2.4, reverse: true },
  { Icon: Navigation, duration: 2.0 },
  { Icon: CableCar, duration: 3.0, reverse: true },
  { Icon: CarFront, duration: 2.1 },
  { Icon: Waves, duration: 3.2, reverse: true },
  { Icon: Sun, duration: 2.7 },
  { Icon: Mountain, duration: 3.1, reverse: true },
];

const laneConfigs: LaneSpinnerConfig[] = [
  { Icon: Plane, duration: 1.8 },
  { Icon: TrainFront, duration: 2.2, reverse: true },
  { Icon: BusFront, duration: 2.0 },
  { Icon: CarFront, duration: 1.7, reverse: true },
  { Icon: Ship, duration: 2.6 },
  { Icon: CableCar, duration: 2.4, reverse: true },
  { Icon: Luggage, duration: 1.9 },
  { Icon: Ticket, duration: 1.8, reverse: true },
  { Icon: MapPin, duration: 2.3 },
  { Icon: Camera, duration: 2.1, reverse: true },
];

const beaconConfigs: IconSpinnerConfig[] = [
  { Icon: Hotel, duration: 3.0 },
  { Icon: Coffee, duration: 2.4, reverse: true },
  { Icon: Trees, duration: 3.2 },
  { Icon: Sun, duration: 2.7, reverse: true },
  { Icon: Mountain, duration: 3.1 },
  { Icon: Waves, duration: 2.9, reverse: true },
  { Icon: Compass, duration: 2.5 },
  { Icon: Globe, duration: 2.8, reverse: true },
  { Icon: Route, duration: 2.6 },
  { Icon: Navigation, duration: 2.2, reverse: true },
];

const panelConfigs: PanelSpinnerConfig[] = [
  { Icon: TicketsPlane, duration: 1.8 },
  { Icon: Ticket, duration: 2.0, delay: 0.12 },
  { Icon: Hotel, duration: 2.4, delay: 0.08 },
  { Icon: Luggage, duration: 2.1, delay: 0.16 },
  { Icon: Camera, duration: 1.9, delay: 0.1 },
  { Icon: Map, duration: 2.3, delay: 0.14 },
  { Icon: ShipWheel, duration: 2.5, delay: 0.18 },
  { Icon: UtensilsCrossed, duration: 2.2, delay: 0.06 },
  { Icon: Plane, duration: 1.7, delay: 0.11 },
  { Icon: TrainFront, duration: 2.0, delay: 0.15 },
];

function HaloIconSpinner({
  Icon,
  duration,
  rings = 2,
}: IconSpinnerConfig) {
  return (
    <div className="relative h-16 w-16">
      <div className="absolute inset-4 rounded-full border border-[color:var(--accent)]/10 bg-background/80" />
      {Array.from({ length: rings }).map((_, index) => (
        <span
          key={index}
          className="absolute rounded-full border border-[color:var(--accent)]/20 animate-ping"
          style={{
            inset: `${index * 4}px`,
            animationDuration: `${duration + index * 0.35}s`,
            animationDelay: `${index * 0.16}s`,
          }}
        />
      ))}
      <div className="absolute inset-0 flex items-center justify-center">
        <Icon className="h-5 w-5 animate-pulse text-[color:var(--accent)]" />
      </div>
    </div>
  );
}

function OrbitIconSpinner({
  Icon,
  duration,
  reverse = false,
}: IconSpinnerConfig) {
  return (
    <div className="relative h-16 w-16">
      <div className="absolute inset-2 rounded-full border border-dashed border-[color:var(--accent)]/22" />
      <div className="absolute inset-5 rounded-full border border-[color:var(--accent)]/10 bg-background/70" />
      <div
        className="absolute inset-0 animate-spin"
        style={{
          animationDuration: `${duration}s`,
          animationDirection: reverse ? "reverse" : "normal",
        }}
      >
        <div className="flex h-full items-start justify-center pt-0.5">
          <div className="h-2.5 w-2.5 rounded-full bg-[color:var(--accent)]" />
        </div>
      </div>
      <div
        className="absolute inset-3 animate-spin"
        style={{
          animationDuration: `${duration * 0.8}s`,
          animationDirection: reverse ? "normal" : "reverse",
        }}
      >
        <div className="flex h-full items-end justify-center pb-0.5">
          <div className="h-1.5 w-1.5 rounded-full bg-[color:var(--accent)]/50" />
        </div>
      </div>
      <div className="absolute inset-0 flex items-center justify-center">
        <Icon className="h-5 w-5 text-[color:var(--accent)]" />
      </div>
    </div>
  );
}

function LaneIconSpinner({
  Icon,
  duration,
  reverse = false,
}: LaneSpinnerConfig) {
  const animationName = reverse
    ? "spinner-demo-lane-reverse"
    : "spinner-demo-lane";

  return (
    <div className="relative h-14 w-20">
      <div className="absolute left-1 top-1/2 h-px w-[calc(100%-0.5rem)] -translate-y-1/2 bg-[color:var(--accent)]/20" />
      <div className="absolute left-2 top-1/2 h-2 w-2 -translate-y-1/2 rounded-full bg-[color:var(--accent)]/40" />
      <div className="absolute right-2 top-1/2 h-2 w-2 -translate-y-1/2 rounded-full border border-[color:var(--accent)]/28 bg-background" />
      <div
        className="absolute top-1/2 -translate-y-1/2"
        style={{
          animation: `${animationName} ${duration}s cubic-bezier(0.45, 0.05, 0.55, 0.95) infinite`,
        }}
      >
        <div className="flex h-8 w-8 items-center justify-center rounded-2xl border border-[color:var(--accent)]/16 bg-background shadow-[0_10px_24px_-20px_rgba(15,23,42,0.5)]">
          <Icon className="h-4 w-4 text-[color:var(--accent)]" />
        </div>
      </div>
    </div>
  );
}

function BeaconIconSpinner({
  Icon,
  duration,
  reverse = false,
}: IconSpinnerConfig) {
  return (
    <div className="relative h-16 w-16">
      <div className="absolute inset-4 rounded-2xl border border-[color:var(--accent)]/10 bg-background/75" />
      <div
        className="absolute inset-0 animate-spin"
        style={{
          animationDuration: `${duration}s`,
          animationDirection: reverse ? "reverse" : "normal",
        }}
      >
        {[0, 1, 2, 3].map((index) => (
          <span
            key={index}
            className="absolute left-1/2 top-1/2 h-2.5 w-2.5 -translate-x-1/2 -translate-y-1/2 rounded-full border border-[color:var(--accent)]/25 bg-background"
            style={{
              transform: `rotate(${index * 90}deg) translateY(-27px)`,
            }}
          />
        ))}
      </div>
      {[0, 1].map((index) => (
        <span
          key={index}
          className="absolute rounded-full border border-[color:var(--accent)]/18 animate-ping"
          style={{
            inset: `${index * 5}px`,
            animationDuration: `${duration + 0.4 + index * 0.3}s`,
            animationDelay: `${index * 0.2}s`,
          }}
        />
      ))}
      <div className="absolute inset-0 flex items-center justify-center">
        <Icon className="h-5 w-5 animate-pulse text-[color:var(--accent)]" />
      </div>
    </div>
  );
}

function PanelIconSpinner({
  Icon,
  duration,
  delay = 0.12,
}: PanelSpinnerConfig) {
  return (
    <div className="relative h-14 w-16 overflow-hidden rounded-2xl border border-[color:var(--accent)]/16 bg-background">
      <div className="absolute inset-x-2 top-2 h-px bg-[color:var(--accent)]/12" />
      <div className="absolute inset-x-2 bottom-2 h-px bg-[color:var(--accent)]/12" />
      <div
        className="absolute inset-y-2 left-2 w-[calc(50%-0.625rem)] origin-left rounded-xl bg-[color:var(--accent)]/12"
        style={{
          animation: `spinner-demo-shutter ${duration}s ease-in-out infinite`,
        }}
      />
      <div
        className="absolute inset-y-2 right-2 w-[calc(50%-0.625rem)] origin-right rounded-xl bg-[color:var(--accent)]/12"
        style={{
          animation: `spinner-demo-shutter ${duration}s ease-in-out infinite`,
          animationDelay: `${delay}s`,
        }}
      />
      <div className="absolute inset-0 flex items-center justify-center">
        <Icon
          className="h-4 w-4 text-[color:var(--accent)]"
          style={{
            animation: `spinner-demo-bob ${Math.max(1.4, duration - 0.2)}s ease-in-out infinite`,
          }}
        />
      </div>
    </div>
  );
}

function toSpinnerArray<T>(
  configs: T[],
  render: (config: T, index: number) => JSX.Element,
): SpinnerComponent[] {
  return configs.map(
    (config, index) =>
      function Spinner() {
        return render(config, index);
      },
  );
}

export const moreTravelSpinners: SpinnerComponent[] = [
  ...toSpinnerArray(haloConfigs, (config) => <HaloIconSpinner {...config} />),
  ...toSpinnerArray(orbitConfigs, (config) => <OrbitIconSpinner {...config} />),
  ...toSpinnerArray(laneConfigs, (config) => <LaneIconSpinner {...config} />),
  ...toSpinnerArray(beaconConfigs, (config) => <BeaconIconSpinner {...config} />),
  ...toSpinnerArray(panelConfigs, (config) => <PanelIconSpinner {...config} />),
];
