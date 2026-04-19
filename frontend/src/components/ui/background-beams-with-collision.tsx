"use client";

import { AnimatePresence, motion } from "motion/react";
import type { CSSProperties, ReactNode, RefObject } from "react";
import { useEffect, useRef, useState } from "react";

function joinClasses(...values: Array<string | undefined | false>) {
  return values.filter(Boolean).join(" ");
}

export function BackgroundBeamsWithCollision({
  children,
  className,
}: {
  children: ReactNode;
  className?: string;
}) {
  const containerRef = useRef<HTMLDivElement>(null);
  const parentRef = useRef<HTMLDivElement>(null);

  const beams = [
    {
      initialX: 10,
      translateX: 10,
      duration: 7,
      repeatDelay: 3,
      delay: 2,
    },
    {
      initialX: 600,
      translateX: 600,
      duration: 3,
      repeatDelay: 3,
      delay: 4,
    },
    {
      initialX: 100,
      translateX: 100,
      duration: 7,
      repeatDelay: 7,
      className: "h-6",
    },
    {
      initialX: 400,
      translateX: 400,
      duration: 5,
      repeatDelay: 14,
      delay: 4,
    },
    {
      initialX: 800,
      translateX: 800,
      duration: 11,
      repeatDelay: 2,
      className: "h-20",
    },
    {
      initialX: 1000,
      translateX: 1000,
      duration: 4,
      repeatDelay: 2,
      className: "h-12",
    },
    {
      initialX: 1200,
      translateX: 1200,
      duration: 6,
      repeatDelay: 4,
      delay: 2,
      className: "h-6",
    },
  ];

  return (
    <div
      ref={parentRef}
      className={joinClasses(
        "relative flex w-full items-center justify-center overflow-hidden bg-gradient-to-b from-background via-background to-muted/40 dark:to-background/10",
        className,
      )}
    >
      {beams.map((beam) => (
        <CollisionMechanism
          key={`${beam.initialX}-beam`}
          beamOptions={beam}
          containerRef={containerRef}
          parentRef={parentRef}
        />
      ))}

      {children}

      <div
        ref={containerRef}
        className="pointer-events-none absolute inset-x-0 bottom-0 h-24 w-full bg-transparent"
        style={{
          boxShadow: "0 -40px 80px rgba(0, 0, 0, 0.08) inset",
        }}
      />
    </div>
  );
}

function CollisionMechanism({
  parentRef,
  containerRef,
  beamOptions = {},
}: {
  containerRef: RefObject<HTMLDivElement | null>;
  parentRef: RefObject<HTMLDivElement | null>;
  beamOptions?: {
    initialX?: number;
    translateX?: number;
    initialY?: number;
    translateY?: number;
    rotate?: number;
    className?: string;
    duration?: number;
    delay?: number;
    repeatDelay?: number;
  };
}) {
  const beamRef = useRef<HTMLDivElement>(null);
  const [collision, setCollision] = useState<{
    detected: boolean;
    coordinates: { x: number; y: number } | null;
  }>({
    detected: false,
    coordinates: null,
  });
  const [beamKey, setBeamKey] = useState(0);
  const [cycleCollisionDetected, setCycleCollisionDetected] = useState(false);

  useEffect(() => {
    const checkCollision = () => {
      if (
        beamRef.current &&
        containerRef.current &&
        parentRef.current &&
        !cycleCollisionDetected
      ) {
        const beamRect = beamRef.current.getBoundingClientRect();
        const containerRect = containerRef.current.getBoundingClientRect();
        const parentRect = parentRef.current.getBoundingClientRect();

        if (beamRect.bottom >= containerRect.top) {
          const relativeX =
            beamRect.left - parentRect.left + beamRect.width / 2;
          const relativeY = beamRect.bottom - parentRect.top;

          setCollision({
            detected: true,
            coordinates: {
              x: relativeX,
              y: relativeY,
            },
          });
          setCycleCollisionDetected(true);
        }
      }
    };

    const animationInterval = setInterval(checkCollision, 50);
    return () => clearInterval(animationInterval);
  }, [cycleCollisionDetected, containerRef, parentRef]);

  useEffect(() => {
    if (collision.detected && collision.coordinates) {
      const resetTimer = window.setTimeout(() => {
        setCollision({ detected: false, coordinates: null });
        setCycleCollisionDetected(false);
      }, 2000);

      const keyTimer = window.setTimeout(() => {
        setBeamKey((previousKey) => previousKey + 1);
      }, 2000);

      return () => {
        window.clearTimeout(resetTimer);
        window.clearTimeout(keyTimer);
      };
    }
  }, [collision]);

  return (
    <>
      <motion.div
        key={beamKey}
        ref={beamRef}
        animate="animate"
        initial={{
          translateY: beamOptions.initialY || "-200px",
          translateX: beamOptions.initialX || "0px",
          rotate: beamOptions.rotate || 0,
        }}
        variants={{
          animate: {
            translateY: beamOptions.translateY || "1800px",
            translateX: beamOptions.translateX || "0px",
            rotate: beamOptions.rotate || 0,
          },
        }}
        transition={{
          duration: beamOptions.duration || 8,
          repeat: Number.POSITIVE_INFINITY,
          repeatType: "loop",
          ease: "linear",
          delay: beamOptions.delay || 0,
          repeatDelay: beamOptions.repeatDelay || 0,
        }}
        className={joinClasses(
          "absolute left-0 top-20 m-auto h-14 w-px rounded-full bg-gradient-to-t from-accent via-[color:var(--accent2)] to-transparent opacity-70",
          beamOptions.className,
        )}
      />
      <AnimatePresence>
        {collision.detected && collision.coordinates ? (
          <Explosion
            key={`${collision.coordinates.x}-${collision.coordinates.y}`}
            seed={
              Math.floor(collision.coordinates.x * 1000) ^
              Math.floor(collision.coordinates.y * 1000)
            }
            style={{
              left: `${collision.coordinates.x}px`,
              top: `${collision.coordinates.y}px`,
              transform: "translate(-50%, -50%)",
            }}
          />
        ) : null}
      </AnimatePresence>
    </>
  );
}

function seeded01(seed: number) {
  let t = (seed + 0x6d2b79f5) | 0;
  t = Math.imul(t ^ (t >>> 15), t | 1);
  t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
  return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
}

function Explosion({
  seed,
  className,
  style,
}: {
  seed: number;
  className?: string;
  style?: CSSProperties;
}) {
  const spans = Array.from({ length: 20 }, (_, index) => {
    const r1 = seeded01(seed ^ (index * 0x9e3779b9));
    const r2 = seeded01(seed ^ (index * 0x85ebca6b));
    const r3 = seeded01(seed ^ (index * 0xc2b2ae35));

    return {
      id: index,
      initialX: 0,
      initialY: 0,
      directionX: Math.floor(r1 * 80 - 40),
      directionY: Math.floor(r2 * -50 - 10),
      duration: r3 * 1.5 + 0.5,
    };
  });

  return (
    <div
      className={joinClasses("absolute z-50 h-2 w-2", className)}
      style={style}
    >
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        transition={{ duration: 1.5, ease: "easeOut" }}
        className="absolute -inset-x-10 top-0 m-auto h-2 w-10 rounded-full bg-gradient-to-r from-transparent via-accent to-transparent blur-sm"
      />
      {spans.map((span) => (
        <motion.span
          key={span.id}
          initial={{ x: span.initialX, y: span.initialY, opacity: 1 }}
          animate={{
            x: span.directionX,
            y: span.directionY,
            opacity: 0,
          }}
          transition={{ duration: span.duration, ease: "easeOut" }}
          className="absolute h-1 w-1 rounded-full bg-gradient-to-b from-accent to-[color:var(--accent2)]"
        />
      ))}
    </div>
  );
}
