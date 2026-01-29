"use client";

import Link from "next/link";
import { Utensils } from "lucide-react";
import { useTranslations } from "next-intl";
import { Button } from "@/components/ui/button";

/**
 * Empty state shown when no meals have been logged for the day.
 * Displays a friendly message and call-to-action to log a meal.
 */
export function EmptyLogState() {
  const t = useTranslations();

  return (
    <div className="flex flex-col items-center justify-center py-12 px-4 text-center">
      <div className="mb-4 rounded-full bg-muted p-4">
        <Utensils className="h-8 w-8 text-muted-foreground" />
      </div>
      <h3 className="mb-2 text-xl font-semibold">{t("dashboard.noMeals")}</h3>
      <p className="mb-6 text-muted-foreground text-lg">{t("logs.noLogs")}</p>
      <Button asChild size="lg" className="text-lg px-8 py-6">
        <Link href="/snap">{t("dashboard.snapMeal")}</Link>
      </Button>
    </div>
  );
}
