"use client";

import { useEffect, useState } from "react";
import { cn } from "@/lib/utils";
import { BrainCircuit, CheckCircle2, AlertCircle } from "lucide-react";

interface ThinkingIndicatorProps {
  thoughts: string[];
  status: "idle" | "connecting" | "streaming" | "complete" | "error";
  className?: string;
}

/**
 * ThinkingIndicator displays the agent's thinking process.
 * Refactored for "Subtle Warmth":
 * - No jumping text (Fixed height container).
 * - No scrollbars (Only generic or latest thought shown).
 * - Subtle "Breathing" animation instead of aggressive bounce.
 */
export function ThinkingIndicator({
  thoughts,
  status,
  className,
}: ThinkingIndicatorProps) {
  const [displayThought, setDisplayThought] = useState("");

  // Update display thought smoothly
  useEffect(() => {
    if (thoughts.length > 0) {
      setDisplayThought(thoughts[thoughts.length - 1]);
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
        "bg-white/95 backdrop-blur-sm shadow-xl border border-zinc-100/20",
        "w-full max-w-sm mx-auto transition-all duration-300",
        className,
      )}
      role="status"
      aria-live="polite"
    >
      {/* Listening/Thinking Animation */}
      {isProcessing && (
        <div className="relative mb-6" aria-hidden="true">
          {/* Outer gentle ripple */}
          <div
            className={cn(
              "absolute inset-0 rounded-full bg-indigo-500/10",
              "animate-[pulse_3s_ease-in-out_infinite]",
            )}
            style={{ transform: "scale(1.5)" }}
          />
          {/* Inner gentle ripple */}
          <div
            className={cn(
              "absolute inset-0 rounded-full bg-indigo-500/20",
              "animate-[pulse_3s_ease-in-out_infinite_1s]",
            )}
            style={{ transform: "scale(1.25)" }}
          />
          {/* Core circle - No bounce, just subtle breathe */}
          <div
            className={cn(
              "relative w-16 h-16 rounded-full",
              "bg-gradient-to-tr from-indigo-600 to-indigo-500",
              "flex items-center justify-center",
              "shadow-lg shadow-indigo-500/20",
              "transition-transform duration-700 ease-in-out",
            )}
          >
            <BrainCircuit className="w-8 h-8 text-white animate-[pulse_3s_ease-in-out_infinite]" />
          </div>
        </div>
      )}

      {/* Completion State */}
      {isComplete && (
        <div className="relative mb-6" aria-hidden="true">
          <div
            className={cn(
              "w-16 h-16 rounded-full",
              "bg-gradient-to-tr from-emerald-500 to-emerald-400",
              "flex items-center justify-center",
              "shadow-lg shadow-emerald-500/30",
              "animate-in zoom-in duration-300",
            )}
          >
            <CheckCircle2 className="w-8 h-8 text-white" />
          </div>
        </div>
      )}

      {/* Error State */}
      {isError && (
        <div className="relative mb-6" aria-hidden="true">
          <div
            className={cn(
              "w-16 h-16 rounded-full",
              "bg-gradient-to-tr from-red-500 to-red-400",
              "flex items-center justify-center",
              "shadow-lg shadow-red-500/30",
            )}
          >
            <AlertCircle className="w-8 h-8 text-white" />
          </div>
        </div>
      )}

      {/* Text Container - Rigid Height to prevent layout shift */}
      <div className="h-16 w-full flex items-center justify-center">
        {isProcessing && (
          <p
            key={displayThought} // Key change triggers animation
            className={cn(
              "text-center text-lg font-medium leading-tight",
              "text-indigo-900", // High contrast/Warmth
              "animate-in fade-in slide-in-from-bottom-1 duration-300",
            )}
          >
            {/* Show 'Connecting...' if no thoughts yet, else show latest thought */}
            {thoughts.length === 0 ? "Connecting..." : displayThought}
          </p>
        )}

        {isComplete && (
          <p className="text-center text-lg font-medium text-emerald-800 animate-in fade-in">
            Analysis complete
          </p>
        )}

        {isError && (
          <p className="text-center text-lg font-medium text-red-700 animate-in fade-in">
            Something went wrong
          </p>
        )}
      </div>
    </div>
  );
}

export default ThinkingIndicator;
