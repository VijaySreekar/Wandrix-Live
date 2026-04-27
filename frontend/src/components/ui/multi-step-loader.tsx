"use client";

import { useEffect, useState } from "react";
import { Check, Loader2 } from "lucide-react";
import { AnimatePresence, motion, useReducedMotion } from "motion/react";

import { cn } from "@/lib/utils";

export type MultiStepLoadingState = {
  text: string;
};

type MultiStepLoaderProps = {
  loadingStates: MultiStepLoadingState[];
  loading: boolean;
  duration?: number;
  mode?: "progress" | "activity";
  loop?: boolean;
};

export function MultiStepLoader({
  loadingStates,
  loading,
  duration = 1600,
  mode = "progress",
  loop = false,
}: MultiStepLoaderProps) {
  const reduceMotion = useReducedMotion();
  const [activeIndex, setActiveIndex] = useState(0);

  useEffect(() => {
    if (!loading || loadingStates.length === 0) {
      return;
    }

    const resetTimeout = window.setTimeout(() => {
      setActiveIndex(0);
    }, 0);
    const interval = window.setInterval(() => {
      setActiveIndex((current) => {
        if (loop) {
          return (current + 1) % loadingStates.length;
        }
        return current >= loadingStates.length - 1 ? current : current + 1;
      });
    }, duration);

    return () => {
      window.clearTimeout(resetTimeout);
      window.clearInterval(interval);
    };
  }, [duration, loading, loadingStates.length, loop]);

  return (
    <AnimatePresence>
      {loading ? (
        <motion.div
          className="absolute inset-0 z-20 flex items-center justify-center bg-[color:color-mix(in_srgb,var(--planner-board-bg)_92%,transparent)] px-6 backdrop-blur-xl"
          initial={reduceMotion ? { opacity: 0 } : { opacity: 0, scale: 0.99 }}
          animate={reduceMotion ? { opacity: 1 } : { opacity: 1, scale: 1 }}
          exit={reduceMotion ? { opacity: 0 } : { opacity: 0, scale: 0.99 }}
          transition={{ duration: reduceMotion ? 0.01 : 0.22 }}
        >
          <div className="w-full max-w-md rounded-2xl border border-[var(--planner-board-border)] bg-[var(--planner-board-card)] p-6 shadow-[var(--chat-shadow-card)]">
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-[color:var(--accent)] text-white">
                <Loader2 className="h-5 w-5 animate-spin" />
              </div>
              <div>
                <p className="font-label text-[10px] uppercase tracking-[0.18em] text-[var(--planner-board-muted-strong)]">
                  Quick Plan
                </p>
                <h3 className="mt-1 text-base font-semibold text-[var(--planner-board-title)]">
                  Building the itinerary
                </h3>
              </div>
            </div>

            <div className="mt-6 space-y-3">
              {loadingStates.map((state, index) => {
                const isDone = mode === "progress" && index < activeIndex;
                const isActive = index === activeIndex;

                return (
                  <div
                    key={state.text}
                    className={cn(
                      "flex items-center gap-3 rounded-xl border px-3 py-3 transition-colors",
                      isActive
                        ? "border-[color:var(--accent)]/35 bg-[color:var(--accent)]/7"
                        : "border-transparent bg-transparent",
                    )}
                  >
                    <div
                      className={cn(
                        "flex h-6 w-6 shrink-0 items-center justify-center rounded-full border text-[11px]",
                        isDone
                          ? "border-[color:var(--accent)] bg-[color:var(--accent)] text-white"
                          : isActive
                            ? "border-[color:var(--accent)] text-[color:var(--accent)]"
                            : "border-[var(--planner-board-border)] text-[var(--planner-board-muted)]",
                      )}
                    >
                      {isDone ? (
                        <Check className="h-3.5 w-3.5" />
                      ) : isActive && mode === "activity" ? (
                        <Loader2 className="h-3.5 w-3.5 animate-spin" />
                      ) : (
                        index + 1
                      )}
                    </div>
                    <p
                      className={cn(
                        "text-sm",
                        isActive || isDone
                          ? "font-semibold text-[var(--planner-board-text)]"
                          : "text-[var(--planner-board-muted)]",
                      )}
                    >
                      {state.text}
                    </p>
                  </div>
                );
              })}
            </div>
          </div>
        </motion.div>
      ) : null}
    </AnimatePresence>
  );
}
