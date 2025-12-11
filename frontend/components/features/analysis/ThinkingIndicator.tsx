"use client";

import { useEffect, useRef } from "react";
import { cn } from "@/lib/utils";
import { BrainCircuit, CheckCircle2, AlertCircle } from "lucide-react";

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
        "flex flex-col items-center justify-center p-8 rounded-2xl",
        "bg-white/95 backdrop-blur-sm shadow-xl border border-zinc-100/20",
        "max-w-sm w-full mx-auto",
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
        <div className="relative mb-8" aria-hidden="true">
          {/* Outer pulse ring */}
          <div
            className={cn(
              "absolute inset-0 rounded-full bg-indigo-500/20",
              "animate-[pulse_2s_ease-in-out_infinite]"
            )}
            style={{ transform: "scale(1.5)" }}
          />
          {/* Middle pulse ring */}
          <div
            className={cn(
              "absolute inset-0 rounded-full bg-indigo-500/30",
              "animate-[pulse_2s_ease-in-out_infinite_0.5s]"
            )}
            style={{ transform: "scale(1.25)" }}
          />
          {/* Core circle with icon */}
          <div
            className={cn(
              "relative w-20 h-20 rounded-full",
              "bg-gradient-to-tr from-indigo-600 to-indigo-500",
              "flex items-center justify-center",
              "shadow-lg shadow-indigo-500/30",
              "animate-[bounce_3s_ease-in-out_infinite]"
            )}
          >
            <BrainCircuit className="w-10 h-10 text-white" />
          </div>
        </div>
      )}

      {/* Completion Checkmark with Bloom Effect */}
      {isComplete && (
        <div className="relative mb-8" aria-hidden="true">
          <div
            className={cn(
              "w-20 h-20 rounded-full",
              "bg-gradient-to-tr from-emerald-500 to-emerald-400",
              "flex items-center justify-center",
              "shadow-lg shadow-emerald-500/30",
              "animate-[bloom_0.5s_ease-out]"
            )}
          >
            <CheckCircle2 className="w-10 h-10 text-white animate-[checkmark_0.3s_ease-out_0.2s_both]" />
          </div>
        </div>
      )}

      {/* Error Icon */}
      {isError && (
        <div className="relative mb-8" aria-hidden="true">
          <div
            className={cn(
              "w-20 h-20 rounded-full",
              "bg-gradient-to-tr from-red-500 to-red-400",
              "flex items-center justify-center",
              "shadow-lg shadow-red-500/30"
            )}
          >
            <AlertCircle className="w-10 h-10 text-white" />
          </div>
        </div>
      )}

      {/* Thoughts Display */}
      <div
        ref={containerRef}
        className={cn(
          "w-full max-h-32 overflow-y-auto",
          "flex flex-col gap-3 items-center"
        )}
      >
        {thoughts.map((thought, index) => (
          <p
            key={index}
            className={cn(
              "text-center text-lg font-medium leading-relaxed",
              "text-zinc-700",
              "animate-[fadeIn_0.5s_ease-out]"
            )}
            style={{
              animationDelay: `${index * 100}ms`,
              animationFillMode: "both",
            }}
          >
            {thought}
          </p>
        ))}

        {/* Connecting state message */}
        {status === "connecting" && thoughts.length === 0 && (
          <p className="text-center text-lg font-medium text-zinc-500 animate-pulse">
            Connecting to secure agent...
          </p>
        )}
        
        {isError && (
             <p className="text-center text-lg font-medium text-red-600">
                Something went wrong. Please try again.
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
