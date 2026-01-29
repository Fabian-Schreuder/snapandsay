"use client";

import { useLocale, useTranslations } from "next-intl";
import type { DietaryLog } from "@/types/log";

interface DailySummaryProps {
  logs: DietaryLog[];
}

/**
 * Daily summary header showing today's date and total calories.
 */
export function DailySummary({ logs }: DailySummaryProps) {
  const t = useTranslations("dashboard");
  const locale = useLocale();
  const totalCalories = logs.reduce((sum, log) => sum + (log.calories || 0), 0);

  const formattedDate = new Date().toLocaleDateString(locale, {
    weekday: "long",
    month: "long",
    day: "numeric",
  });

  return (
    <div className="mb-6">
      <h1 className="text-2xl font-bold capitalize">{formattedDate}</h1>
      <p className="text-lg text-muted-foreground">
        {logs.length > 0
          ? t.rich("total", {
              calories: totalCalories,
              count: (chunks) => (
                <span className="font-medium text-foreground">{chunks}</span>
              ),
            })
          : t("startTracking")}
      </p>
    </div>
  );
}
