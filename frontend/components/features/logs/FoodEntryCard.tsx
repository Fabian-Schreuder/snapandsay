"use client";

import Image from "next/image";
import { useRouter } from "next/navigation";
import { AlertTriangle } from "lucide-react";
import type { DietaryLog } from "@/types/log";

interface FoodEntryCardProps {
  log: DietaryLog;
  onClick?: () => void;
}

/**
 * Get public URL for an image stored in Supabase Storage.
 */
function getImageUrl(path: string): string {
  const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
  // Use raw_uploads bucket for images
  return `${supabaseUrl}/storage/v1/object/public/raw_uploads/${path}`;
}

/**
 * Format timestamp to human-readable time (e.g., "12:30 PM").
 */
function formatTime(isoString: string): string {
  return new Date(isoString).toLocaleTimeString([], {
    hour: "numeric",
    minute: "2-digit",
    hour12: true,
  });
}

/**
 * FoodEntryCard displays a single meal log entry.
 * Tapping navigates to the log detail page.
 *
 * Layout:
 * ┌─────────────────────────────────────────┐
 * │ ┌──────┐  Description / Transcript     │
 * │ │ IMG  │  Time                          │
 * │ │80x80 │                    [cal badge] │
 * │ └──────┘        [⚠️ if needs_review]    │
 * └─────────────────────────────────────────┘
 */
import { useTranslations } from "next-intl";

export function FoodEntryCard({ log, onClick }: FoodEntryCardProps) {
  const t = useTranslations("logs");
  const router = useRouter();
  const displayText =
    log.title || log.description || log.transcript || t("defaultTitle");
  const imageUrl = log.image_url || getImageUrl(log.image_path);
  const timeDisplay = formatTime(log.created_at);

  const handleClick = () => {
    if (onClick) {
      onClick();
    } else {
      router.push(`/log/${log.id}`);
    }
  };

  return (
    <button
      onClick={handleClick}
      className={`flex w-full items-center gap-4 p-4 min-h-[100px] rounded-xl text-card-foreground shadow-sm hover:shadow-md transition-shadow text-left focus:outline-none focus-visible:ring-2 focus-visible:ring-ring ${
        log.status === "invalid"
          ? "bg-destructive/10 border-2 border-destructive/20"
          : "bg-card"
      }`}
      type="button"
    >
      {/* Thumbnail */}
      <div className="relative h-20 w-20 flex-shrink-0 overflow-hidden rounded-lg bg-muted">
        <Image
          src={imageUrl}
          alt={displayText}
          fill
          className={`object-cover ${log.status === "invalid" ? "opacity-50 grayscale" : ""}`}
          sizes="80px"
        />
        {log.status === "invalid" && (
          <div className="absolute inset-0 flex items-center justify-center bg-black/10">
            <AlertTriangle className="h-8 w-8 text-destructive" />
          </div>
        )}
      </div>

      {/* Content */}
      <div className="flex flex-1 flex-col gap-1 min-w-0">
        <p
          className={`text-lg font-medium leading-snug line-clamp-2 ${log.status === "invalid" ? "text-destructive" : ""}`}
        >
          {log.status === "invalid" ? "Invalid Entry" : displayText}
        </p>
        <div className="flex items-center gap-2 text-sm text-muted-foreground">
          <span>{timeDisplay}</span>
          {log.needs_review && log.status !== "invalid" && (
            <AlertTriangle
              className="h-4 w-4 text-amber-500"
              aria-label="Needs review"
            />
          )}
          {log.status === "invalid" && log.description && (
            <span className="text-xs text-destructive/80 line-clamp-1">
              {log.description.replace(/^\[Invalid\]:\s*/i, "").trim()}
            </span>
          )}
        </div>
      </div>

      {/* Calories Badge */}
      {log.calories != null && (
        <div className="flex-shrink-0 rounded-full bg-primary/10 px-3 py-1 text-sm font-medium text-primary">
          {log.calories} cal
        </div>
      )}
    </button>
  );
}
