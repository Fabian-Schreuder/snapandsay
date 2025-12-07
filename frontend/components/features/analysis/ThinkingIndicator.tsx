"use client";

import { useEffect, useRef } from "react";
import { cn } from "@/lib/utils";

interface ThinkingIndicatorProps {
  thoughts: string[];
  status: "idle" | "connecting" | "streaming" | "complete" | "error";
  className?: string;
}

/**
 * ThinkingIndicator displays the agent's thinking process with a "listening pulse"
 * animation (per UX spec - NOT a spinner). Thoughts fade in with smooth transitions.
 *
 * Senior-friendly: 20px minimum text, high contrast, 6s minimum visibility.
 */
export function ThinkingIndicator({
  thoughts,
  status,
  className,
}: ThinkingIndicatorProps) {
  const containerRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to latest thought
  useEffect(() => {
    if (containerRef.current) {
      containerRef.current.scrollTop = containerRef.current.scrollHeight;
    }
  }, [thoughts]);

  if (status === "idle") {
    return null;
  }

  const isProcessing = status === "connecting" || status === "streaming";
  const isComplete = status === "complete";
  const isError = status === "error";

  return (
    <div
      className={cn(
        "flex flex-col items-center justify-center p-6 rounded-2xl",
        "bg-zinc-50 border border-zinc-200",
        className
      )}
      role="status"
      aria-live="polite"
      aria-label={
        isProcessing
          ? "AI is analyzing your meal"
          : isComplete
            ? "Analysis complete"
            : "An error occurred"
      }
    >
      {/* Listening Pulse Animation */}
      {isProcessing && (
        <div className="relative mb-6" aria-hidden="true">
          {/* Outer pulse ring */}
          <div
            className={cn(
              "absolute inset-0 rounded-full bg-emerald-400/30",
              "animate-[pulse_2s_ease-in-out_infinite]"
            )}
            style={{ transform: "scale(1.5)" }}
          />
          {/* Middle pulse ring */}
          <div
            className={cn(
              "absolute inset-0 rounded-full bg-emerald-400/40",
              "animate-[pulse_2s_ease-in-out_infinite_0.5s]"
            )}
            style={{ transform: "scale(1.25)" }}
          />
          {/* Core circle with food icon */}
          <div
            className={cn(
              "relative w-16 h-16 rounded-full",
              "bg-gradient-to-br from-emerald-400 to-emerald-600",
              "flex items-center justify-center",
              "animate-[bounce_3s_ease-in-out_infinite]"
            )}
          >
            <span className="text-2xl">🍽️</span>
          </div>
        </div>
      )}

      {/* Completion Checkmark with Bloom Effect */}
      {isComplete && (
        <div className="relative mb-6" aria-hidden="true">
          <div
            className={cn(
              "w-16 h-16 rounded-full",
              "bg-gradient-to-br from-emerald-400 to-emerald-600",
              "flex items-center justify-center",
              "animate-[bloom_0.5s_ease-out]"
            )}
          >
            <svg
              className="w-8 h-8 text-white animate-[checkmark_0.3s_ease-out_0.2s_both]"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              strokeWidth={3}
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M5 13l4 4L19 7"
              />
            </svg>
          </div>
        </div>
      )}

      {/* Error Icon */}
      {isError && (
        <div className="relative mb-6" aria-hidden="true">
          <div
            className={cn(
              "w-16 h-16 rounded-full",
              "bg-gradient-to-br from-red-400 to-red-600",
              "flex items-center justify-center"
            )}
          >
            <span className="text-2xl">😔</span>
          </div>
        </div>
      )}

      {/* Thoughts Display */}
      <div
        ref={containerRef}
        className={cn(
          "w-full max-h-32 overflow-y-auto",
          "flex flex-col gap-2"
        )}
      >
        {thoughts.map((thought, index) => (
          <p
            key={index}
            className={cn(
              "text-center text-xl font-medium",
              "text-slate-900",
              "animate-[fadeIn_0.2s_ease-in-out]"
            )}
            style={{
              animationDelay: `${index * 50}ms`,
              animationFillMode: "both",
            }}
          >
            {thought}
          </p>
        ))}

        {/* Connecting state message */}
        {status === "connecting" && thoughts.length === 0 && (
          <p className="text-center text-xl font-medium text-slate-600">
            Connecting...
          </p>
        )}
      </div>

      {/* Screen reader announcement for completion */}
      {isComplete && (
        <span className="sr-only">
          Analysis complete. Your meal has been logged.
        </span>
      )}
    </div>
  );
}

export default ThinkingIndicator;
